"""
Telegram-адаптер на aiogram 3.x.

Отвечает только за транспорт: ведёт диалог-меню (имя → телефон → запрос),
собирает данные и отдаёт их в LeadService в виде единой модели Lead.
Бизнес-логики здесь нет — только сбор и нормализация.
"""
from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.core.models import Lead
from app.core.service import LeadService

log = logging.getLogger(__name__)


class LeadForm(StatesGroup):
    """Состояния короткого диалога-меню сбора заявки."""

    name = State()
    phone = State()
    request = State()


class TelegramAdapter:
    """Реализация MessengerAdapter для Telegram."""

    def __init__(self, bot: Bot, service: LeadService) -> None:
        self._bot = bot
        self._service = service
        self._dp = Dispatcher()
        self._register_handlers()

    # --- реализация интерфейса MessengerAdapter ---

    async def listen(self) -> None:
        """Запустить long-polling. Блокирует выполнение до остановки."""
        log.info("TelegramAdapter запущен, начинаю polling…")
        # Сбрасываем "хвост" старых апдейтов, чтобы не обрабатывать устаревшее.
        await self._bot.delete_webhook(drop_pending_updates=True)
        await self._dp.start_polling(self._bot)

    async def send(self, chat_id: Any, text: str) -> None:
        """Отправить сообщение пользователю."""
        await self._bot.send_message(chat_id=chat_id, text=text)

    def normalize(self, raw: dict[str, Any]) -> Lead:
        """Собрать Lead из собранных в диалоге данных."""
        return Lead(
            name=raw.get("name", "").strip(),
            phone=raw.get("phone", "").strip(),
            request_text=raw.get("request", "").strip(),
            source="telegram",
            external_user_id=str(raw.get("user_id")) if raw.get("user_id") else None,
            external_username=raw.get("username"),
        )

    # --- внутренние хэндлеры диалога ---

    def _register_handlers(self) -> None:
        dp = self._dp

        @dp.message(Command("start"))
        async def cmd_start(message: Message, state: FSMContext) -> None:
            """Старт диалога: приветствие + вопрос имени."""
            await state.clear()
            await message.answer(
                "Здравствуйте! Я помогу оформить заявку. Это займёт 30 секунд.\n\n"
                "Как вас зовут?",
                reply_markup=ReplyKeyboardRemove(),
            )
            await state.set_state(LeadForm.name)

        @dp.message(Command("cancel"))
        async def cmd_cancel(message: Message, state: FSMContext) -> None:
            """Отмена диалога в любой момент."""
            await state.clear()
            await message.answer(
                "Заявка отменена. Чтобы начать заново — отправьте /start.",
                reply_markup=ReplyKeyboardRemove(),
            )

        @dp.message(LeadForm.name, F.text)
        async def step_name(message: Message, state: FSMContext) -> None:
            """Приняли имя → просим телефон (кнопкой или текстом)."""
            await state.update_data(name=message.text)
            phone_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📞 Отправить мой номер", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await message.answer(
                "Приятно! Оставьте номер телефона для связи.\n"
                "Можно нажать кнопку ниже или написать номер вручную.",
                reply_markup=phone_kb,
            )
            await state.set_state(LeadForm.phone)

        @dp.message(LeadForm.phone, F.contact)
        async def step_phone_contact(message: Message, state: FSMContext) -> None:
            """Телефон пришёл через кнопку контакта."""
            await state.update_data(phone=message.contact.phone_number)
            await self._ask_request(message, state)

        @dp.message(LeadForm.phone, F.text)
        async def step_phone_text(message: Message, state: FSMContext) -> None:
            """Телефон ввели текстом."""
            await state.update_data(phone=message.text)
            await self._ask_request(message, state)

        @dp.message(LeadForm.request, F.text)
        async def step_request(message: Message, state: FSMContext) -> None:
            """Получили суть запроса → формируем и регистрируем заявку."""
            await state.update_data(request=message.text)
            data = await state.get_data()
            data["user_id"] = message.from_user.id
            data["username"] = message.from_user.username

            # Нормализуем в единую модель и отдаём в бизнес-логику.
            lead = self.normalize(data)
            try:
                await self._service.register_lead(lead)
                await message.answer(
                    "Спасибо! Заявка принята ✅\n"
                    "Мы свяжемся с вами в ближайшее время.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception:
                # Любая ошибка обработки НЕ должна ронять бота.
                log.exception("Ошибка при регистрации заявки")
                await message.answer(
                    "Произошла техническая ошибка, но мы уже разбираемся. "
                    "Пожалуйста, попробуйте ещё раз через /start.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            finally:
                await state.clear()

        @dp.message()
        async def fallback(message: Message) -> None:
            """Любое сообщение вне диалога — подсказываем начать."""
            await message.answer("Чтобы оставить заявку, отправьте /start.")

    async def _ask_request(self, message: Message, state: FSMContext) -> None:
        """Общий шаг: после телефона спрашиваем суть запроса."""
        await message.answer(
            "Спасибо! Опишите суть запроса.\n"
            "Для запчастей укажите марку/модель или VIN.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(LeadForm.request)
