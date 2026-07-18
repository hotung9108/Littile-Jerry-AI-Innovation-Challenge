"""
Tìm kiếm / truy vấn Institutional Memory bằng ngôn ngữ tự nhiên.

Cách hoạt động (RAG đơn giản, không cần vector DB để chạy MVP):
  1. Retrieval: chấm điểm liên quan giữa câu hỏi và từng KnowledgeItem bằng
     so khớp từ khóa (đơn giản, không cần embedding — dễ chạy ngay).
  2. Synthesis: nếu có LLM, đưa top-N item liên quan nhất cho LLM để tổng hợp
     thành 1 câu trả lời tự nhiên, có trích dẫn nguồn. Nếu không có LLM,
     trả về danh sách item liên quan để người dùng tự đọc.

Ghi chú nâng cấp sau này: thay bước (1) bằng vector search (pgvector,
Qdrant, Pinecone...) để retrieval chính xác hơn với câu hỏi diễn đạt khác
từ ngữ so với dữ liệu gốc.
"""
import re
from typing import List

from app.knowledge_models import KnowledgeItem, SearchResult
from app.llm_client import chat_json, is_configured, LLMNotConfigured
from app import knowledge_store

_STOPWORDS = {
    "là", "của", "và", "có", "cho", "các", "một", "trong", "khi", "được",
    "này", "đã", "sẽ", "gì", "ai", "nào", "như", "thế", "với", "về", "tại",
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[\wÀ-ỹ]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _score(item: KnowledgeItem, query_tokens: List[str]) -> int:
    haystack = " ".join(
        filter(None, [item.summary, item.project, item.team, item.owner, item.channel_or_doc])
    ).lower()
    return sum(haystack.count(tok) for tok in query_tokens)


def retrieve(query: str, project: str = None, team: str = None, top_k: int = 8) -> List[KnowledgeItem]:
    tokens = _tokenize(query)
    candidates = knowledge_store.list_items(project=project, team=team, limit=1000)

    scored = [(item, _score(item, tokens)) for item in candidates]
    scored = [pair for pair in scored if pair[1] > 0] or [(item, 0) for item in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [item for item, _ in scored[:top_k]]


_SYSTEM_PROMPT = (
    "Bạn là trợ lý tra cứu tri thức nội bộ (Institutional Memory) cho một tổ chức "
    "phi lợi nhuận. Dựa CHỈ vào danh sách knowledge item được cung cấp (JSON), hãy "
    "trả lời câu hỏi của người dùng bằng tiếng Việt, súc tích, chính xác. "
    "Nếu dữ liệu không đủ để trả lời, hãy nói rõ là chưa có thông tin thay vì bịa. "
    "Luôn nêu rõ nguồn liên quan (channel_or_doc) khi trích dẫn thông tin.\n\n"
    'CHỈ trả về JSON: {"answer": "..."}'
)


def search_knowledge(query: str, project: str = None, team: str = None) -> SearchResult:
    items = retrieve(query, project=project, team=team)

    answer = None
    if is_configured() and items:
        try:
            import json

            payload = json.dumps(
                [i.model_dump(mode="json") for i in items], ensure_ascii=False
            )
            parsed = chat_json(_SYSTEM_PROMPT, f"Câu hỏi: {query}\n\nDữ liệu:\n{payload}")
            answer = parsed.get("answer")
        except (LLMNotConfigured, Exception):
            answer = None

    return SearchResult(query=query, answer=answer, items=items)
