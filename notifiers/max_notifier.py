import logging
import aiohttp

log = logging.getLogger(__name__)

MAX_API = "https://platform-api.max.ru"


class MaxNotifier:
    """Отправляет сообщение менеджеру через MAX."""

    def __init__(self, token: str, manager_user_id):
        self.token = token
        self.manager_user_id = manager_user_id

    async def send(self, text: str) -> bool:
        if not self.token or not self.manager_user_id:
            log.warning("MAX: нет токена или id менеджера — пропускаю отправку")
            return False

        url = f"{MAX_API}/messages"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
        }
        params = {"user_id": self.manager_user_id}
        payload = {"text": text}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, params=params, headers=headers, json=payload
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        log.error("MAX send failed [%s]: %s", response.status, body)
                        return False
                    return True
        except Exception as e:
            log.exception("MAX send error: %s", e)
            return False