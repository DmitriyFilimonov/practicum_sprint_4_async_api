from logging import error, warning

from functools import wraps
from time import sleep
from typing import Generator
import redis
import requests

import psycopg


def coroutine(func):
    @wraps(func)
    def start(*args, **kwargs) -> Generator:
        gen = func(*args, **kwargs)
        next(gen)
        return gen

    return start


RETRYABLE_ERRORS = (
    psycopg.OperationalError,
    ConnectionError,
    requests.exceptions.ConnectionError,
    psycopg.OperationalError,
    redis.ConnectionError
)


def backoff(start_sleep_time=1, factor=2, border_sleep_time=10):
    """
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать время ожидания на каждой итерации
    :param border_sleep_time: максимальное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            delay = start_sleep_time
            attempt = 0

            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not isinstance(e, RETRYABLE_ERRORS):
                        error(
                            f'"{inner.__name__}": {error}.\nЗавершение процесса.',
                        )
                        raise

                    delay = min(start_sleep_time * (factor**attempt), border_sleep_time)
                    attempt += 1

                    if delay >= border_sleep_time:
                        error(
                            f'Не удается выполнить "{inner.__name__}". Превышено максимальное время ожидания: {border_sleep_time} сек.',
                            f"\nВыполнено попыток: {attempt}.",
                        )

                        raise

                    warning(
                        f'Ошибка выполнения "{inner.__name__}": {error}.'
                        f"\nПовторная попытка через {delay:.0f} сек.",
                    )

                    sleep(delay)

        return inner

    return func_wrapper
