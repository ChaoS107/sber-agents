import os
from pathlib import Path


def load_env_file() -> None:
    """Загружает переменные из .env файла."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value


# Загружаем .env при импорте модуля
load_env_file()

# Критичные переменные
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY не задан в переменных окружения")

MODEL_NAME = os.environ.get("MODEL_NAME")
if not MODEL_NAME:
    raise ValueError("MODEL_NAME не задан в переменных окружения")

# Опциональные переменные
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

