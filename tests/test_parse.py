from bot.parse import extract_ask_query, parse_ask_update


BOT = "knowledge_bot"
CHAT = -1001234567890


def _msg(text: str, **extra):
    message = {
        "message_id": 10,
        "text": text,
        "chat": {"id": CHAT, "type": "supergroup"},
        "from": {"id": 42, "is_bot": False, "username": "alice"},
        "entities": [],
    }
    message.update(extra)
    return message


def test_extract_ask_command():
    assert extract_ask_query(_msg("/ask что такое rag"), BOT) == "что такое rag"
    assert extract_ask_query(_msg(f"/ask@{BOT} hello"), BOT) == "hello"


def test_extract_mention():
    text = f"@{BOT} как оформить отпуск"
    message = _msg(
        text,
        entities=[{"type": "mention", "offset": 0, "length": len(f"@{BOT}")}],
    )
    assert extract_ask_query(message, BOT) == "как оформить отпуск"


def test_ignores_plain_text():
    assert extract_ask_query(_msg("просто вопрос без бота"), BOT) is None


def test_parse_respects_allowlist():
    update = {"message": _msg("/ask тест", ephemeral_message_id=77)}
    ctx = parse_ask_update(update, allowed_chat_ids={CHAT}, bot_username=BOT)
    assert ctx is not None
    assert ctx.query == "тест"
    assert ctx.ephemeral_message_id == 77

    blocked = parse_ask_update(update, allowed_chat_ids={999}, bot_username=BOT)
    assert blocked is None
