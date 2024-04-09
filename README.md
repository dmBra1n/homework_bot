# Homework Bot

## Описание проекта

Telegram Bot для отслеживания изменений статуса проверки домашней работы на Yandex Practicum

Фунциональность бота:
- Раз в 10 минут обращается к API practicum.yandex и проверяет статус отправленной на ревью домашней работы;
- При обновлении статуса проверки, отправляет соответствующее уведомление в Telegram;
- Логгирует свою работу и сообщает о важных проблемах сообщением в Telegram.

#### Инструменты и стек:
![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=ffdd54)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=flat-square&logo=telegram&logoColor=white)

## Локальный запуск проекта
1. Склонировать репозиторий
2. Установить зависимости с помощью `pip install -r requirements.txt`
3. В корне проекта создать и заполнить файл _.env_ следующим образом:

    ```env
    PRACTICUM_TOKEN=<токен_Яндекс_практикум>
    TELEGRAM_TOKEN =<токен_Telegram_bot>
    TELEGRAM_CHAT_ID=<id_Telegram_чата>
    ```
    Получить <a href="https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a" target="_blank">токен</a> ЯндексПрактикум

5. Запустить проект с помощью `python homework_bot.py`
