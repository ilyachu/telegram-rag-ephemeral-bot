# Подключение своей RAG-базы

Бот не хранит документы и не знает вашу схему индексов.
Единственная точка входа — `ask_rag(question, settings) -> RagAnswer` в `bot/rag.py`.

## Вариант A: HTTP JSON (без правок кода)

В `.env`:

```env
RAG_HTTP_URL=https://your-service.example.com/v1/ask
RAG_HTTP_TOKEN=optional_bearer_token
RAG_HTTP_TIMEOUT_SEC=60
```

Контракт запроса:

```http
POST /v1/ask
Content-Type: application/json
Authorization: Bearer <token>   # если задан

{"question":"Как оформить отпуск?"}
```

Контракт ответа:

```json
{
  "answer": "Краткий ответ…",
  "sources": [
    {"title": "Политика отпусков", "url": "https://intranet.example/docs/leave"}
  ]
}
```

Поля-синонимы: `text` вместо `answer`; `name` вместо `title`.

## Вариант B: прямой вызов в коде

```python
# bot/rag.py
def ask_rag(question: str, settings: Settings) -> RagAnswer:
    hits = your_vector_store.search(question, k=5)
    answer = your_llm.generate(question, context=hits)
    return RagAnswer(
        text=answer,
        sources=[RagSource(title=h.title, url=h.url) for h in hits],
    )
```

## Вариант C: LangChain / LlamaIndex

Оберните существующий chain/query engine:

```python
def ask_rag(question: str, settings: Settings) -> RagAnswer:
    result = chain.invoke({"question": question})
    return RagAnswer(text=result["answer"], sources=[...])
```

## Что бот делает с ответом

1. Экранирует HTML.
2. Добавляет блок «Источники» (до 5 ссылок).
3. Укладывает текст в лимит Telegram (4096 символов).
4. Редактирует то же скрытое / DM-сообщение — один пузырь на весь ответ.

## Чего нет в шаблоне (намеренно)

- стриминга токенов в Telegram (можно добавить поверх `edit_*`);
- аутентификации пользователей сверх allowlist чатов;
- проксирования через корпоративный egress;
- вашего промпта, эмбеддингов, чанков, оценок релевантности.

Это зона вашей RAG. Шаблон — только транспорт.
