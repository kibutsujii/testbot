"""
Единая модель заявки (Lead).

Это "ядро" системы: модель НЕ зависит ни от Telegram, ни от Google Sheets.
Любой адаптер мессенджера приводит входящее сообщение к этому виду,
а любое хранилище умеет его сохранять. Так мы сможем добавлять VK / MAX /
WhatsApp и менять БД, не трогая бизнес-логику.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# Статусы заявки. На MVP используется только NEW, но фиксируем перечень,
# чтобы потом не плодить "магические строки".
STATUS_NEW = "новая"


@dataclass
class Lead:
    """Одна заявка от клиента.

    Поля специально простые (строки/даты), чтобы их легко было сложить
    в строку Google Sheets или в любую БД.
    """

    name: str                       # Имя клиента
    phone: str                      # Телефон клиента
    request_text: str               # Суть запроса (для запчастей — марка/VIN)
    source: str = "telegram"        # Источник заявки
    status: str = STATUS_NEW        # Статус (на MVP всегда "новая")
    created_at: datetime = field(default_factory=datetime.now)

    # Технические поля — пригодятся позже (дедупликация, ответы клиенту).
    external_user_id: str | None = None   # ID пользователя в мессенджере
    external_username: str | None = None  # @username, если есть

    def as_row(self) -> list[str]:
        """Представление заявки одной строкой таблицы (порядок колонок фиксирован)."""
        return [
            self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            self.source,
            self.name,
            self.phone,
            self.request_text,
            self.status,
        ]

    @staticmethod
    def row_header() -> list[str]:
        """Заголовок таблицы — должен совпадать по порядку с as_row()."""
        return ["Дата/время", "Источник", "Имя", "Телефон", "Запрос", "Статус"]

    def as_message(self) -> str:
        """Человекочитаемый текст для уведомления менеджеру."""
        return (
            "🔔 <b>Новая заявка</b>\n\n"
            f"👤 <b>Имя:</b> {self.name}\n"
            f"📞 <b>Телефон:</b> {self.phone}\n"
            f"📝 <b>Запрос:</b> {self.request_text}\n"
            f"🌐 <b>Источник:</b> {self.source}\n"
            f"🕒 <b>Время:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
