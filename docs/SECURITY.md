# Security notes

## Secrets

- Never commit `.env`, tokens, chat allowlists with real production ids you consider sensitive, or API keys.
- Rotate any token that was pasted into chat, CI logs, or screenshots.
- Prefer OS secret stores / systemd `EnvironmentFile` with `0600` permissions in production.

## Least privilege

- Restrict `ALLOWED_CHAT_IDS` to the groups that should use the bot.
- Give the bot only the admin rights it needs for ephemeral replies.
- Do not log full question text if your knowledge base is confidential; default logging stores user/chat ids only.

## Supply chain

- Pin dependency ranges in `requirements.txt`.
- Review `RAG_HTTP_URL` — it receives user questions from Telegram.

## Reporting

Open a GitHub issue for security problems that do not include live secrets.
If you accidentally published a token, revoke it first, then open the issue.
