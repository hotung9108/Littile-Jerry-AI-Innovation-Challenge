# Weekly Report Agent — Báo cáo tuần tự động

Demo Agent workflow: lấy báo cáo hằng ngày (mock giả lập Jira) → chuẩn hóa →
phân tích → tổng hợp thành **báo cáo tuần** gồm 6 mục:

1. Kết quả nổi bật
2. Công việc đã hoàn thành
3. Công việc đang thực hiện
4. Khó khăn
5. Quyết định
6. Công việc tiếp theo

## Kiến trúc

```
weekly-report-agent/
├── backend/                  # Python (FastAPI)
│   ├── app/
│   │   ├── main.py           # API endpoints
│   │   ├── config.py         # Đọc biến môi trường (.env)
│   │   ├── models.py         # Schema dùng chung (Pydantic)
│   │   ├── mock_data.py      # Sinh dữ liệu MOCK mô phỏng Jira
│   │   ├── jira_client.py    # Adapter gọi Jira REST API thật
│   │   └── agent/
│   │       ├── normalizer.py # Bước 1: chuẩn hóa dữ liệu
│   │       ├── analyzer.py   # Bước 2: phân loại (done/in-progress/blocker/decision)
│   │       ├── summarizer.py # Bước 3: viết báo cáo (LLM hoặc rule-based)
│   │       └── workflow.py   # Orchestrator: nối 3 bước trên lại
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── index.html            # Giao diện demo: mock data -> gọi backend -> hiển thị
```

**Điểm quan trọng:** `mock_data.py` và `jira_client.py` đều trả về cùng một
schema (`DailyReport` / `DailyReportItem`), nên các bước `normalizer`,
`analyzer`, `summarizer` không cần biết dữ liệu đến từ đâu. Khi chuyển sang
dữ liệu thật, chỉ cần đổi tham số `source=jira` — không phải sửa logic agent.

## Cài đặt & chạy thử (dùng mock data)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # để mặc định DATA_SOURCE=mock là chạy được ngay
uvicorn app.main:app --reload --port 8000
```

Mở `frontend/index.html` bằng trình duyệt (double-click hoặc `python -m http.server`
trong thư mục `frontend`), rồi:
1. Bấm **"1. Tạo dữ liệu mock"** — sinh dữ liệu giả lập báo cáo Jira hằng ngày.
2. Bấm **"2. Tạo báo cáo tuần"** — Agent chạy pipeline và hiển thị báo cáo 6 mục.

Có thể test nhanh bằng `curl` mà không cần frontend:

```bash
curl -X POST "http://localhost:8000/api/mock/generate?days=5"
curl -X POST "http://localhost:8000/api/reports/weekly?source=mock&days=5"
```

Xem API docs tự động (Swagger UI) tại: `http://localhost:8000/docs`

## Bật LLM để viết báo cáo tự nhiên hơn (tuỳ chọn)

Mặc định hệ thống dùng bộ tóm tắt rule-based (template), không cần API key,
vẫn tạo ra báo cáo hợp lệ. Muốn Claude viết lại các gạch đầu dòng súc tích
hơn, thêm vào `.env`:

```
ANTHROPIC_API_KEY=sk-ant-xxxx
```

## Chuyển sang dữ liệu Jira thật

1. Tạo API token tại https://id.atlassian.com/manage-profile/security/api-tokens
2. Cập nhật `.env`:
   ```
   DATA_SOURCE=jira
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_API_TOKEN=xxxx
   JIRA_PROJECT_KEY=PROJ
   ```
3. Gọi lại API với `source=jira`:
   ```
   POST /api/reports/weekly?source=jira&days=5
   ```

`jira_client.py` dùng Jira REST API v3 (`/rest/api/3/search` với JQL) để lấy
các issue được cập nhật trong N ngày gần nhất, kèm comment cuối để dò tìm
khó khăn/quyết định (dựa trên từ khóa — có thể tinh chỉnh thêm theo quy ước
của team, ví dụ gắn label riêng `blocker` / `decision` trong Jira để chính
xác hơn thay vì dò từ khóa trong comment).

## Hướng phát triển tiếp theo

- Lưu báo cáo vào database (Postgres) thay vì bộ nhớ tạm, để xem lại lịch sử.
- Thêm xác thực JWT cho API.
- Cron job tự động chạy vào cuối mỗi tuần và gửi báo cáo qua Slack/Email.
- Cho phép gắn nhãn Jira riêng (`blocker`, `decision`) để phân loại chính xác
  hơn thay vì dò từ khóa trong comment.
- Thêm bộ lọc theo từng thành viên/dự án khi có nhiều team.
