"""
Cấu hình chung cho backend.
Đọc biến môi trường từ file .env (nếu có) hoặc từ hệ thống.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Nguồn dữ liệu: "mock" (dữ liệu giả) hoặc "jira" (dữ liệu thật từ Jira)
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "mock")

    # Thông tin kết nối Jira (chỉ cần khi DATA_SOURCE="jira")
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "PROJ")

    # LLM dùng để viết báo cáo (tuỳ chọn). Nếu không có API key,
    # hệ thống sẽ tự động dùng bộ tóm tắt rule-based (không cần LLM).
    # LLM_PROVIDER: "anthropic" | "groq" | "none"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # CORS - cho phép frontend (mock HTML/JS) gọi API
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")


settings = Settings()