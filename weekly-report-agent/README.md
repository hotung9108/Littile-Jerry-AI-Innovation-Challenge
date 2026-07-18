**Nguyên tắc thiết kế xuyên suốt:** mọi nguồn dữ liệu (mock hoặc thật) đều
trả về **cùng một schema** (`DailyReport`/`DailyReportItem` cho task
management, `RawEvent` cho Organizational Brain). Nhờ vậy các bước xử lý
(normalize/analyze/summarize, extract/search/risk) không cần biết dữ liệu
đến từ đâu — chuyển từ mock sang thật chỉ cần đổi tham số nguồn (`source`/
`mode`), không phải sửa logic agent.

## Cài đặt & chạy thử (mock data, không cần cấu hình gì)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Xem API docs tự động (Swagger UI) tại: `http://localhost:8000/docs`

### Test Weekly Report Agent

Mở `frontend/index.html` bằng trình duyệt, hoặc test bằng `curl`:

```bash
curl -X POST "http://localhost:8000/api/mock/generate?days=5"
curl -X POST "http://localhost:8000/api/reports/weekly?source=mock&days=5"

# Lọc theo thành viên / dự án
curl -X POST "http://localhost:8000/api/reports/weekly?source=mock&days=5&assignee=Minh&project=PROJ"

# Xem lịch sử báo cáo đã lưu (cần cấu hình DATABASE_URL)
curl "http://localhost:8000/api/reports/weekly/history"
```

### Test Organizational Brain

```bash
# 1. Ingest dữ liệu mock từ cả 4 kênh: Slack, Email, Meeting, Google Docs
curl -X POST "http://localhost:8000/api/brain/ingest?source=all&mode=mock&days=7"

# 2. Trích xuất tri thức (decision/action_item/blocker/relationship/fact)
curl -X POST "http://localhost:8000/api/brain/extract"

# 3. Xem danh sách tri thức đã trích xuất (có thể lọc)
curl "http://localhost:8000/api/brain/items?type=blocker&limit=10"

# 4. Tìm kiếm bằng ngôn ngữ tự nhiên
curl "http://localhost:8000/api/brain/search?q=team%20gay%20quy%20gap%20kho%20khan%20gi"

# 5. Phát hiện rủi ro / phụ thuộc
curl "http://localhost:8000/api/brain/risks"

# 6. Tóm tắt onboarding cho tình nguyện viên mới
curl "http://localhost:8000/api/brain/onboarding?project=Chi%E1%BA%BFn%20d%E1%BB%8Bch%20g%C3%A2y%20qu%E1%BB%B9%20M%C3%B9a%20%C4%90%C3%B4ng"
```

## Bật LLM (Groq hoặc Anthropic) — tuỳ chọn

Mặc định hệ thống dùng logic **rule-based** (không cần LLM, không cần API
key) cho cả tóm tắt báo cáo tuần lẫn trích xuất tri thức — luôn chạy được
ngay. Muốn AI viết/hiểu tự nhiên hơn, thêm vào `.env`:

```bash
# Dùng Groq (nhanh, có gói miễn phí)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxx        # lấy tại https://console.groq.com/keys
GROQ_MODEL=llama-3.3-70b-versatile

# Hoặc dùng Claude (Anthropic)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxx
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Nếu gọi LLM lỗi (sai key, hết quota, timeout...), hệ thống tự động fallback
về rule-based, không làm sập luồng.

## Lưu lịch sử vào Postgres — tuỳ chọn

Mặc định dữ liệu chỉ lưu tạm trong bộ nhớ (mất khi restart server). Để lưu
lâu dài và xem lại lịch sử, thêm vào `.env`:

```bash
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/weekly_report
```

Bảng sẽ tự động được tạo khi backend khởi động (không cần chạy migration
thủ công). Có 2 bảng: `weekly_reports` và `knowledge_items`.

## Cron tự động: báo cáo tuần + cảnh báo rủi ro

Bật scheduler chạy nền, tự tạo báo cáo tuần và quét rủi ro theo lịch, gửi
qua Slack/Email:

```bash
ENABLE_SCHEDULER=true
WEEKLY_REPORT_CRON=0 17 * * FRI     # mặc định: Thứ Sáu 17h
RISK_CHECK_CRON=0 9 * * *           # mặc định: 9h sáng mỗi ngày

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password           # dùng App Password nếu là Gmail
REPORT_EMAIL_RECIPIENTS=a@org.com,b@org.com
```

## Chuyển sang dữ liệu thật

### Jira (Weekly Report Agent)

1. Tạo API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. Cập nhật `.env`:
```bash
   DATA_SOURCE=jira
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_API_TOKEN=xxxx
   JIRA_PROJECT_KEY=PROJ
```
3. Gọi API với `source=jira`:
```bash
   curl -X POST "http://localhost:8000/api/reports/weekly?source=jira&days=5"
```

`jira_client.py` ưu tiên đọc **nhãn (label) riêng** `blocker` / `decision`
gắn trên issue để phân loại chính xác; chỉ dò từ khóa trong comment khi
issue không có nhãn phù hợp.

### Slack / Email / Meeting / Google Docs (Organizational Brain)

Mỗi nguồn có adapter thật sẵn cấu trúc trong `app/sources/real_sources.py`,
chỉ cần cài thêm SDK + điền credentials, rồi gọi `mode=real` thay vì `mock`:

```bash
# Slack — cần: pip install slack_sdk
SLACK_BOT_TOKEN=xoxb-xxxx
SLACK_CHANNEL_IDS=C0123,C0456

# Email — dùng thư viện chuẩn (imaplib), không cần cài thêm
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_USER=your-email@gmail.com
EMAIL_IMAP_PASSWORD=app-password

# Meeting transcript — đọc file .txt trong thư mục (đổi thành gọi API
# Otter.ai/Fireflies.ai/Zoom nếu team dùng công cụ đó)
MEETING_TRANSCRIPTS_DIR=/path/to/transcripts

# Google Docs — cần: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
GOOGLE_DRIVE_FOLDER_ID=xxxx
```

```bash
curl -X POST "http://localhost:8000/api/brain/ingest?source=slack&mode=real&days=7"
```

## Hướng phát triển tiếp theo

- Thay retrieval từ khóa (keyword) trong `brain/search.py` bằng vector
  search (pgvector, Qdrant...) để tìm kiếm chính xác hơn với câu hỏi diễn
  đạt khác từ ngữ so với dữ liệu gốc.
- Thêm xác thực JWT / phân quyền theo team cho API.
- Nhận diện quan hệ `related_to` tự động giữa các KnowledgeItem (liên kết
  issue Jira với quyết định/blocker liên quan trong Slack/Meeting).
- Giao diện xem Institutional Memory dạng dashboard thay vì chỉ JSON API.
- Migration tool chính thức (Alembic) thay vì `create_all` khi schema
  database thay đổi nhiều.