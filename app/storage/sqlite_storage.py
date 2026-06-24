"""
Бонус: хранилище на SQLite (файловая БД, нулевая настройка).

Данный класс НИЧЕГО не требует кроме стандартной библиотеки Python.
Чтобы переключиться на него — поставьте STORAGE_BACKEND=sqlite в .env.
Это наглядно показывает, что благодаря интерфейсу Storage базу данных
можно менять без правок в core/ и адаптерах.
"""
from __future__ import annotations

import asyncio
import logging
import sqlite3

from app.core.models import Lead

log = logging.getLogger(__name__)


class SqliteStorage:
    """Сохраняет заявки в локальный файл SQLite."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _init_sync(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at   TEXT NOT NULL,
                    source       TEXT NOT NULL,
                    name         TEXT NOT NULL,
                    phone        TEXT NOT NULL,
                    request_text TEXT NOT NULL,
                    status       TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _save_sync(self, lead: Lead) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO leads "
                "(created_at, source, name, phone, request_text, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    lead.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    lead.source,
                    lead.name,
                    lead.phone,
                    lead.request_text,
                    lead.status,
                ),
            )
            conn.commit()

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)
        log.info("SQLite готов: %s", self._db_path)

    async def save(self, lead: Lead) -> None:
        await asyncio.to_thread(self._save_sync, lead)
        log.info("Заявка сохранена в SQLite: %s / %s", lead.name, lead.phone)
