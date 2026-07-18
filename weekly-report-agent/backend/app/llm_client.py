"""
Client LLM dùng chung cho toàn hệ thống (weekly report summarizer +
Organizational Brain extraction/search/risk agents).

Hỗ trợ Groq và Anthropic qua 1 hàm duy nhất `chat_json()`, luôn yêu cầu
model trả về JSON hợp lệ. Nếu không có key nào được cấu hình, gọi hàm này
sẽ raise LLMNotConfigured — nơi gọi (caller) chịu trách nhiệm fallback
sang logic rule-based, để không làm sập luồng chính.
"""
import json
from typing import Optional

from app.config import settings


class LLMNotConfigured(Exception):
    pass


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[: -3].strip()
    return text


def _call_anthropic(system_prompt: str, user_content: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _call_groq(system_prompt: str, user_content: str) -> str:
    import requests

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def chat_json(system_prompt: str, user_content: str) -> dict:
    """Gọi LLM theo LLM_PROVIDER hiện tại, trả về dict đã parse từ JSON."""
    provider = settings.LLM_PROVIDER

    if provider == "groq" and settings.GROQ_API_KEY:
        raw = _call_groq(system_prompt, user_content)
    elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        raw = _call_anthropic(system_prompt, user_content)
    else:
        raise LLMNotConfigured(
            "Chưa cấu hình LLM_PROVIDER + API key tương ứng trong .env"
        )

    return json.loads(_strip_json_fences(raw))


def is_configured() -> bool:
    if settings.LLM_PROVIDER == "groq":
        return bool(settings.GROQ_API_KEY)
    if settings.LLM_PROVIDER == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    return False
