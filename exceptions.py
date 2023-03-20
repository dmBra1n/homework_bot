class InvalidResponseAPI(Exception):
    """Ошибка запроса к API."""
    pass


class InvalidCodeStatus(Exception):
    """Не верный код ответа"""
    pass


class TelegramMessageError(Exception):
    """Ошибка отправки сообщения в Telegram"""
    pass
