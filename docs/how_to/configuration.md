# How-To: Configuration

## Configure environment variables
Settings are loaded from `.env` through `src/config.py`.

Common keys:
- `GEMINI_API_KEY` (optional)
- `GOOGLE_API_KEY` (optional fallback)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` (defined but not primary runtime path today)

## Edit `.env`
```bash
nano .env
```

## Validate configuration path
```bash
./venv/bin/python -c "from src.config import settings; print(settings.gemini_api_key is not None)"
```

## Notes
- Keep secrets out of git (`.env` is ignored).
- Missing Gemini keys should still allow fallback regulation answers.
