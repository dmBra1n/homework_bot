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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения в Telegram чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено!')
    except Exception as error:
        logging.error(f'Ошибка в отправке сообщения: {error}')
        raise TelegramMessageError(f'Ошибка в отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logging.error(f'Ошибка запроса основного API: {error}')
        raise InvalidResponseAPI(f'Ошибка запроса основного API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise InvalidCodeStatus(f'Статус кода {response.status_code}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API не является словарем')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('homeworks не возвращаются в виде списка')
    return response.get('homeworks')


def parse_status(homework):
    """Проверяет статуса домашней работы"""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        raise KeyError('В ответе нет ключа homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют переменные окружения.')
        sys.exit('Критическая ошибка! Отсутствуют токены')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                send_message(bot, parse_status(homeworks[0]))
            else:
                logger.debug('Статус домашней работы не изменился')
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        filename='main.log',
        filemode='w',
        format='%(asctime)s [%(levelname)s] %(message)s'

    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

    main()
