# telegram-rag-ephemeral-bot

Готовый каркас Telegram-бота для **приватных ответов в группе** и подключения **вашей уже существующей RAG-базы**.

Идея: у вас есть поиск/генерация по документам. Этот репозиторий даёт транспорт в Telegram — команды, скрытые сообщения в группе, запасной путь в личку — а RAG вы подключаете одним блоком.

## Что внутри

- long polling на чистом Python (stdlib + `httpx`)
- триггеры: `/ask` из меню команд, `/ask вопрос`, `@bot вопрос`
- **ephemeral** (скрытые) статусы и ответы в группе — видит только автор вопроса
- fallback в **личку**, если скрытый ответ в группе недоступен (бот не админ)
- заглушка `ask_rag()` — сюда вставляете вызов своего API
- без секретов в репозитории: только `.env.example`

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните BOT_TOKEN, BOT_USERNAME, ALLOWED_CHAT_IDS
python -m bot
```

Регистрация команды `/ask` как ephemeral (скрытая для остальных в чате):

```bash
python scripts/setup_commands.py
```

## Подключение RAG

Откройте [`bot/rag.py`](bot/rag.py) и реализуйте `ask_rag(question: str) -> RagAnswer`.

Минимальный контракт:

```python
@dataclass
class RagAnswer:
    text: str
    sources: list[RagSource]  # optional links shown under the answer
```

Примеры адаптеров — в [`docs/RAG_INTEGRATION.md`](docs/RAG_INTEGRATION.md): HTTP JSON endpoint, LangChain, собственный векторный индекс.

Бот **не** знает вашу схему хранения. Он только передаёт строку вопроса и ждёт текст ответа.

## Как работают приватные ответы в группе

Подробно: [`docs/EPHEMERAL.md`](docs/EPHEMERAL.md).

| Способ задать вопрос | Вопрос видят все? | Ответ |
|---|---|---|
| `/ask` из **меню команд** | Нет (ephemeral command) | Скрытый в группе (если API позволяет) |
| Набрали `/ask …` текстом | Да | Скрытый, если бот админ; иначе личка |
| `@bot …` | Да | Скрытый, если бот админ; иначе личка |

Рекомендации:

1. Сделайте бота **администратором** группы — тогда скрытые ответы работают и на `@упоминания`.
2. Попросите участников один раз написать боту `/start` в личке — иначе DM-fallback не доставится.
3. Зарегистрируйте `/ask` через `setup_commands.py` с `scope=chat` и ephemeral-флагом.

## Переменные окружения

См. [`.env.example`](.env.example). В git не коммитьте `.env`.

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN` | токен от @BotFather |
| `BOT_USERNAME` | username без `@` |
| `ALLOWED_CHAT_IDS` | список id групп через запятую |
| `RAG_HTTP_URL` | опционально: URL вашего ask-endpoint |
| `RAG_HTTP_TOKEN` | опционально: Bearer для вашего API |

## Структура

```
bot/
  __main__.py      # polling loop
  config.py        # env
  parse.py         # извлечение вопроса из update
  telegram_api.py  # вызовы Bot API
  ephemeral.py     # скрытые сообщения + DM fallback
  rag.py           # ← ПОДКЛЮЧИТЕ СВОЙ RAG ЗДЕСЬ
  handlers.py      # оркестрация ask → progress → answer
scripts/
  setup_commands.py
docs/
  EPHEMERAL.md
  RAG_INTEGRATION.md
tests/
  test_parse.py
```

## Ограничения Telegram (важно)

- Скрытое сообщение в группе без прав админа обычно требует `ephemeral_message_id` исходной команды (окно ~15 секунд).
- Обычный `@mention` **не** даёт этот id → без админки бота ответ уходит в личку.
- Публичные ответы в группу этот шаблон **не** шлёт намеренно: только private ephemeral или DM.

## Лицензия

MIT. Код — учебный каркас. Паттерны ephemeral-ответов проверены на практике в проде, здесь переписаны без привязки к конкретному продукту и без секретов.
