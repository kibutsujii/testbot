"""
Конфигурация приложения.

Все секреты и настройки читаются из переменных окружения (.env).
Никакого хардкода токенов в коде — это и безопаснее, и удобнее при деплое.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Загружаем .env в переменные окружения один раз при импорте модуля.
load_dotenv()


def _require(name: str) -> str:
    """Вернуть обязательную переменную окружения или упасть с понятной ошибкой."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Не задана обязательная переменная окружения {name}. "
            f"Проверь свой .env файл (см. .env.example)."
        )
    return value


@dataclass(frozen=True)
class Config:
    """Неизменяемый объект конфигурации, собранный из окружения."""

    # Telegram
    bot_token: str
    manager_chat_id: int

    # Хранилище
    storage_backend: str  # "google_sheets" | "sqlite"

    # Google Sheets
    google_sheet_id: str
    google_worksheet_name: str
    google_credentials_file: str

    # SQLite
    sqlite_path: str

    # Логи
    log_level: str

    @staticmethod
    def load() -> "Config":
        """Собрать конфиг из переменных окружения."""
        backend = os.getenv("STORAGE_BACKEND", "google_sheets").strip().lower()

        # Google-настройки обязательны только если реально используем Sheets.
        google_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        google_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "service_account.json")
        if backend == "google_sheets":
            google_sheet_id = _require("GOOGLE_SHEET_ID")

        return Config(
            bot_token=_require("BOT_TOKEN"),
            manager_chat_id=int(_require("MANAGER_CHAT_ID")),
            storage_backend=backend,
            google_sheet_id=google_sheet_id,
            google_worksheet_name=os.getenv("GOOGLE_WORKSHEET_NAME", "Заявки"),
            google_credentials_file=google_credentials_file,
            sqlite_path=os.getenv("SQLITE_PATH", "leads.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
