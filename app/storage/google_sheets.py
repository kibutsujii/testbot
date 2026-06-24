"""
Реализация хранилища на Google Sheets.

gspread — синхронная библиотека, поэтому все блокирующие вызовы
оборачиваем в asyncio.to_thread, чтобы не блокировать event loop бота.
"""
from __future__ import annotations

import asyncio
import logging

import gspread
from google.oauth2.service_account import Credentials

from app.core.models import Lead

log = logging.getLogger(__name__)

# Минимально необходимые права: таблицы + файлы Drive.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsStorage:
    """Сохраняет каждую заявку отдельной строкой в указанный лист."""

    def __init__(
        self,
        credentials_file: str,
        sheet_id: str,
        worksheet_name: str,
    ) -> None:
        self._credentials_file = credentials_file
        self._sheet_id = sheet_id
        self._worksheet_name = worksheet_name
        self._worksheet: gspread.Worksheet | None = None

    def _connect_sync(self) -> gspread.Worksheet:
        """Синхронно подключиться к таблице и вернуть нужный лист."""
        creds = Credentials.from_service_account_file(
            self._credentials_file, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(self._sheet_id)

        # Берём лист по имени; если его нет — создаём.
        try:
            worksheet = spreadsheet.worksheet(self._worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=self._worksheet_name, rows=1000, cols=10
            )

        # Если лист пустой — добавляем заголовок.
        if not worksheet.get_all_values():
            worksheet.append_row(Lead.row_header(), value_input_option="USER_ENTERED")

        return worksheet

    async def init(self) -> None:
        """Подключиться один раз при старте и закэшировать лист."""
        self._worksheet = await asyncio.to_thread(self._connect_sync)
        log.info("Google Sheets подключён: лист '%s'", self._worksheet_name)

    async def save(self, lead: Lead) -> None:
        """Добавить заявку одной строкой."""
        if self._worksheet is None:
            # На случай если init() не вызывался — подключимся лениво.
            await self.init()
        assert self._worksheet is not None
        await asyncio.to_thread(
            self._worksheet.append_row,
            lead.as_row(),
            value_input_option="USER_ENTERED",
        )
        log.info("Заявка сохранена в Google Sheets: %s / %s", lead.name, lead.phone)
