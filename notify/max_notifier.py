from __future__ import annotations

import logging

import aiohttp

from app.core.models import Lead
from app.notify.base import Notifier

log = logging.getLogger(__name__)

MAX_API = "https://platform-api.max.ru"


class MaxNotifier(Notifier):
    """Уведомление менеджеру в MAX. Реализует тот же интерфейс, что TelegramNotifier."""

    def __init__(self, token: str, manager_user_id: int) -> None:
        self._token = token
        self._manager_user_id = manager_user_id

    async def notify_new_lead(self, lead: Lead) -> None:
        text = self._format(lead)
        url = f"{MAX_API}/messages"
        headers = {"Authorization": self._token, "Content-Type": "application/json"}
        params = {"user_id": self._manager_user_id}
        payload = {"text": text}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, params=params, headers=headers, json=payload
                ) as r:
                    if r.status != 200:
                        body = await r.text()
                        log.error("MAX: уведомление не ушло [%s]: %s", r.status, body)
        except Exception as e:
            log.exception("MAX: ошибка отправки уведомления: %s", e)

    @staticmethod
    def _format(lead: Lead) -> str:
        lines = [
            f"Новая заявка №{lead.lead_number}",
            f"Источник: {lead.source}",
            f"Имя: {lead.name}",
            f"Телефон: {lead.phone}",
        ]
        if getattr(lead, "brand", None):
            lines.append(f"Авто: {lead.brand} {getattr(lead, 'model', '')} {getattr(lead, 'year', '')}".strip())
        if getattr(lead, "vin", None):
            lines.append(f"VIN: {lead.vin}")
        if getattr(lead, "request_text", None):
            lines.append(f"Запрос: {lead.request_text}")
        return "\n".join(lines)