import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (InvalidCodeStatus, InvalidResponseAPI,
                        TelegramMessageError)

logging.basicConfig(
    filename='main.log',
    filemode='w',
    format='%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность токенов."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing_tokens = []
    for token in tokens:
        if not tokens.get(token):
            missing_tokens.append(token)
    if missing_tokens:
        logger.critical(f'Отсутствующие токены: {missing_tokens}')
        return False
    return True


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено!')
    except Exception as error:
        logger.error(f'Ошибка в отправке сообщения: {error}')
        raise TelegramMessageError(f'Ошибка в отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logger.error(f'Ошибка запроса основного API: {error}')
        raise InvalidResponseAPI(f'Ошибка запроса основного API: {error}')
    if response.status_code != HTTPStatus.OK:
        logger.critical(
            f'Ошибка ответа API. Код ответа: {response.status_code}. '
            f'Параметры: {ENDPOINT}, {HEADERS}, {payload}'
        )
        raise InvalidCodeStatus(f'Статус кода {response.status_code}')
    try:
        return response.json()
    except ValueError as error:
        raise ValueError(f'Возникала ошибка при преобразовании JSON: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API не является словарем')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('homeworks не возвращаются в виде списка')
    if 'current_date' not in response:
        raise KeyError('В ответе нет current_date')
    return response.get('homeworks')


def parse_status(homework):
    """Проверяет статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        raise KeyError('В ответе нет ключа homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Неизвестный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Критическая ошибка! Отсутствуют токены')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    sent_message = ''
    sent_error = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            timestamp = response.get('current_date', timestamp)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != sent_message:
                    send_message(bot, message)
                sent_message = message
            else:
                logger.debug('Статус домашней работы не изменился')
        except Exception as error:
            message_error = f'Сбой в работе программы: {error}'
            send_message(bot, message_error)
            logger.error(message_error)
            if message_error != sent_error:
                send_message(bot, message_error)
                sent_message = message_error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    # Перенес наверх, иначе падает pytest
    # Вопрос: а где лучше размещать блок кода с logger?
    # В main или просто в начале файла?

    # logging.basicConfig(
    #     filename='main.log',
    #     filemode='w',
    #     format='%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s'
    # )
    # logger = logging.getLogger(__name__)
    # logger.setLevel(logging.DEBUG)
    # handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(handler)

    main()
