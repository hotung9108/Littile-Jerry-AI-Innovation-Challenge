"""
Cấu hình chung cho backend.
Đọc biến môi trường từ file .env (nếu có) hoặc từ hệ thống.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes")


class Settings:
    # Nguồn dữ liệu cho weekly report (task tool): "mock" hoặc "jira"
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "mock")

    # --- Jira (task management) ---
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "PROJ")

    # --- Slack (Organizational Brain source) ---
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL_IDS: str = os.getenv("SLACK_CHANNEL_IDS", "")  # "C0123,C0456"

    # --- Email (Organizational Brain source, đọc qua IMAP) ---
    EMAIL_IMAP_HOST: str = os.getenv("EMAIL_IMAP_HOST", "")
    EMAIL_IMAP_USER: str = os.getenv("EMAIL_IMAP_USER", "")
    EMAIL_IMAP_PASSWORD: str = os.getenv("EMAIL_IMAP_PASSWORD", "")

    # --- Meeting transcripts (Organizational Brain source) ---
    MEETING_TRANSCRIPTS_DIR: str = os.getenv("MEETING_TRANSCRIPTS_DIR", "")

    # --- Google Docs (Organizational Brain source) ---
    GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

    # --- Database (Postgres) — tuỳ chọn, nếu trống thì dùng bộ nhớ tạm ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # --- LLM (Groq / Anthropic) — tuỳ chọn, nếu trống thì dùng rule-based ---
    # LLM_PROVIDER: "anthropic" | "groq" | "none"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Thông báo: Slack webhook + Email SMTP ---
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    REPORT_EMAIL_RECIPIENTS: str = os.getenv("REPORT_EMAIL_RECIPIENTS", "")

    # --- Cron scheduler ---
    ENABLE_SCHEDULER: bool = _bool("ENABLE_SCHEDULER", "false")
    WEEKLY_REPORT_CRON: str = os.getenv("WEEKLY_REPORT_CRON", "0 17 * * FRI")
    RISK_CHECK_CRON: str = os.getenv("RISK_CHECK_CRON", "0 9 * * *")

    # --- CORS ---
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")


settings = Settings()
