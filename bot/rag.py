"""
Подключение вашей RAG-базы.

Замените тело ask_rag() на вызов своего API / пайплайна.
Контракт наружу для бота — только RagAnswer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from .config import Settings


@dataclass(frozen=True)
class RagSource:
    title: str
    url: str | None = None


@dataclass(frozen=True)
class RagAnswer:
    text: str
    sources: list[RagSource] = field(default_factory=list)


def ask_rag(question: str, settings: Settings) -> RagAnswer:
    """
    >>> Точка интеграции.

    Варианты:
    1) HTTP: задайте RAG_HTTP_URL (+ опционально RAG_HTTP_TOKEN) — используется адаптер ниже.
    2) Код: замените эту функцию на прямой вызов вашего клиента (LangChain, LlamaIndex, свой сервис).

    Ожидаемый HTTP JSON (пример):
      POST {RAG_HTTP_URL}
      Authorization: Bearer {RAG_HTTP_TOKEN}   # если задан
      {"question": "..."}

      200:
      {
        "answer": "текст ответа",
        "sources": [{"title": "Док", "url": "https://..."}]
      }
    """
    question = (question or "").strip()
    if not question:
        return RagAnswer(text="Пустой вопрос. Напишите /ask ваш вопрос")

    if settings.rag_http_url:
        return _ask_via_http(question, settings)

    # --- ЗАГЛУШКА: удалите и подключите свою базу ---
    return RagAnswer(
        text=(
            "RAG ещё не подключён.\n\n"
            "Откройте bot/rag.py и реализуйте ask_rag(), "
            "либо задайте RAG_HTTP_URL в .env.\n\n"
            f"Ваш вопрос был: {question}"
        ),
        sources=[],
    )


def _ask_via_http(question: str, settings: Settings) -> RagAnswer:
    headers = {"Content-Type": "application/json"}
    if settings.rag_http_token:
        headers["Authorization"] = f"Bearer {settings.rag_http_token}"

    with httpx.Client(timeout=settings.rag_http_timeout_sec) as client:
        response = client.post(
            settings.rag_http_url,  # type: ignore[arg-type]
            json={"question": question},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    answer = str(data.get("answer") or data.get("text") or "").strip()
    if not answer:
        raise RuntimeError("RAG HTTP response has empty answer")

    sources: list[RagSource] = []
    for item in data.get("sources") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or "Источник").strip()
        url = item.get("url")
        sources.append(RagSource(title=title, url=str(url) if url else None))

    return RagAnswer(text=answer, sources=sources)
