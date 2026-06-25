import logging

log = logging.getLogger(__name__)


class ManagerNotifier:
    """Отправляет уведомление о заявке менеджеру в ОДИН выбранный канал."""

    def __init__(
        self,
        channel: str,
        telegram_bot=None,
        telegram_chat_id=None,
        max_notifier=None,
        vk_notifier=None,
    ):
        self.channel = (channel or "telegram").lower()
        self.telegram_bot = telegram_bot
        self.telegram_chat_id = telegram_chat_id
        self.max_notifier = max_notifier
        self.vk_notifier = vk_notifier

    async def notify(self, text: str) -> bool:
        try:
            if self.channel == "telegram":
                if not self.telegram_bot or not self.telegram_chat_id:
                    log.error("Telegram: нет bot или chat_id")
                    return False
                await self.telegram_bot.send_message(self.telegram_chat_id, text)
                return True

            elif self.channel == "max":
                if not self.max_notifier:
                    log.error("MAX: нет notifier")
                    return False
                return await self.max_notifier.send(text)

            elif self.channel == "vk":
                if not self.vk_notifier:
                    log.error("VK: нет notifier")
                    return False
                return await self.vk_notifier.send(text)

            else:
                log.error("Неизвестный MANAGER_CHANNEL: %s", self.channel)
                return False

        except Exception as e:
            log.exception("Уведомление менеджеру (%s) не ушло: %s", self.channel, e)
            return False