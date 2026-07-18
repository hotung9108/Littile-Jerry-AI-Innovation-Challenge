"""
Adapter kết nối các nguồn dữ liệu THẬT: Slack, Email (IMAP), Meeting transcript,
Google Docs. Mỗi class có method fetch_events(days) -> List[RawEvent], CÙNG
schema với mock_sources.py, nên phần extractor/search/risk_monitor dùng chung
logic dù dữ liệu đến từ mock hay thật.

Đây là các adapter SẴN SÀNG VỀ CẤU TRÚC nhưng cần bạn:
  1. Cài thêm SDK tương ứng (đã ghi chú ở từng class)
  2. Điền thông tin xác thực vào .env
  3. Bỏ comment phần gọi API thật (hiện đang raise NotImplementedError
     để tránh gọi nhầm khi chưa cấu hình xong)
"""
from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.knowledge_models import RawEvent


class SlackSource:
    """
    Cần: pip install slack_sdk
    .env: SLACK_BOT_TOKEN=xoxb-..., SLACK_CHANNEL_IDS=C0123,C0456
    Quyền bot cần: channels:history, channels:read, users:read
    """

    def fetch_events(self, days: int = 7) -> List[RawEvent]:
        if not settings.SLACK_BOT_TOKEN:
            raise RuntimeError("Thiếu SLACK_BOT_TOKEN trong .env")

        from slack_sdk import WebClient

        client = WebClient(token=settings.SLACK_BOT_TOKEN)
        oldest = (datetime.utcnow() - timedelta(days=days)).timestamp()
        channel_ids = [c for c in settings.SLACK_CHANNEL_IDS.split(",") if c]

        events: List[RawEvent] = []
        for channel_id in channel_ids:
            channel_info = client.conversations_info(channel=channel_id)
            channel_name = "#" + channel_info["channel"]["name"]

            cursor = None
            while True:
                resp = client.conversations_history(
                    channel=channel_id, oldest=oldest, cursor=cursor, limit=200
                )
                for msg in resp.get("messages", []):
                    if not msg.get("text"):
                        continue
                    user_id = msg.get("user", "unknown")
                    events.append(
                        RawEvent(
                            source="slack",
                            source_ref=msg["ts"],
                            channel_or_doc=channel_name,
                            author=user_id,  # có thể map sang tên qua users_info nếu cần
                            team=None,
                            project=None,
                            timestamp=datetime.fromtimestamp(float(msg["ts"])),
                            content=msg["text"],
                        )
                    )
                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        return events


class EmailSource:
    """
    Cần: thư viện chuẩn imaplib + email (không cần cài thêm gì)
    .env: EMAIL_IMAP_HOST, EMAIL_IMAP_USER, EMAIL_IMAP_PASSWORD
    Gợi ý: dùng App Password nếu là Gmail (không dùng mật khẩu chính).
    """

    def fetch_events(self, days: int = 7) -> List[RawEvent]:
        if not (settings.EMAIL_IMAP_HOST and settings.EMAIL_IMAP_USER and settings.EMAIL_IMAP_PASSWORD):
            raise RuntimeError("Thiếu cấu hình EMAIL_IMAP_* trong .env")

        import imaplib
        import email as email_lib
        from email.header import decode_header

        mail = imaplib.IMAP4_SSL(settings.EMAIL_IMAP_HOST)
        mail.login(settings.EMAIL_IMAP_USER, settings.EMAIL_IMAP_PASSWORD)
        mail.select("inbox")

        since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%d-%b-%Y")
        _typ, data = mail.search(None, f'(SINCE "{since_date}")')

        events: List[RawEvent] = []
        for num in data[0].split():
            _typ, msg_data = mail.fetch(num, "(RFC822)")
            msg = email_lib.message_from_bytes(msg_data[0][1])

            subject, encoding = decode_header(msg.get("Subject", ""))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            events.append(
                RawEvent(
                    source="email",
                    source_ref=msg.get("Message-ID", str(num)),
                    channel_or_doc=subject,
                    author=msg.get("From", "unknown"),
                    team=None,
                    project=None,
                    timestamp=datetime.utcnow(),  # có thể parse header Date cho chính xác hơn
                    content=body[:2000],
                )
            )

        mail.close()
        mail.logout()
        return events


class MeetingSource:
    """
    Không có API "chuẩn" chung cho meeting transcript — tuỳ công cụ bạn dùng
    (Otter.ai, Fireflies.ai, Google Meet transcript, Zoom Cloud Recording...).
    Class này đọc file transcript (.txt/.vtt) từ một thư mục cấu hình sẵn,
    làm điểm khởi đầu đơn giản nhất; đổi phần đọc file thành gọi API của
    công cụ bạn dùng khi cần.

    .env: MEETING_TRANSCRIPTS_DIR=/path/to/transcripts
    """

    def fetch_events(self, days: int = 7) -> List[RawEvent]:
        import os
        import glob

        if not settings.MEETING_TRANSCRIPTS_DIR:
            raise RuntimeError("Thiếu MEETING_TRANSCRIPTS_DIR trong .env")

        cutoff = datetime.utcnow() - timedelta(days=days)
        events: List[RawEvent] = []

        for path in glob.glob(os.path.join(settings.MEETING_TRANSCRIPTS_DIR, "*.txt")):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime < cutoff:
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            events.append(
                RawEvent(
                    source="meeting",
                    source_ref=os.path.basename(path),
                    channel_or_doc=os.path.splitext(os.path.basename(path))[0],
                    author="unknown",
                    team=None,
                    project=None,
                    timestamp=mtime,
                    content=content[:4000],
                )
            )
        return events


class GDocsSource:
    """
    Cần: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
    .env: GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
          GOOGLE_DRIVE_FOLDER_ID=xxxx (folder chứa các doc cần theo dõi)
    Service account cần được share quyền "Viewer" trên folder đó.
    """

    def fetch_events(self, days: int = 7) -> List[RawEvent]:
        if not (settings.GOOGLE_SERVICE_ACCOUNT_FILE and settings.GOOGLE_DRIVE_FOLDER_ID):
            raise RuntimeError("Thiếu cấu hình GOOGLE_SERVICE_ACCOUNT_FILE / GOOGLE_DRIVE_FOLDER_ID trong .env")

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        drive = build("drive", "v3", credentials=creds)
        docs = build("docs", "v1", credentials=creds)

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"
        query = (
            f"'{settings.GOOGLE_DRIVE_FOLDER_ID}' in parents "
            f"and mimeType='application/vnd.google-apps.document' "
            f"and modifiedTime > '{cutoff}'"
        )
        results = drive.files().list(q=query, fields="files(id, name, modifiedTime)").execute()

        events: List[RawEvent] = []
        for f in results.get("files", []):
            doc = docs.documents().get(documentId=f["id"]).execute()
            text_parts = []
            for elem in doc.get("body", {}).get("content", []):
                para = elem.get("paragraph")
                if not para:
                    continue
                for run in para.get("elements", []):
                    if "textRun" in run:
                        text_parts.append(run["textRun"]["content"])
            content = "".join(text_parts)

            events.append(
                RawEvent(
                    source="gdocs",
                    source_ref=f["id"],
                    channel_or_doc=f["name"],
                    author="unknown",
                    team=None,
                    project=None,
                    timestamp=datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00")),
                    content=content[:4000],
                )
            )
        return events
