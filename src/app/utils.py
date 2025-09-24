import datetime
import logging
import time


def connection_problems_decorator(func):
    """
    Декоратор, который бесконечно повторяет выполнение функции
    до тех пор, пока она не выполнится успешно, перехватывая и
    выводя любые возникающие исключения.

    Аргументы:
        func (callable): Функция, которую нужно декорировать.

    Возвращает:
        callable: Обернутая функция, которая будет продолжать
        вызывать оригинальную функцию до тех пор, пока она не
        выполнится без ошибок.
    """
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as err:
                print(f'Exception in {func.__name__} \n {err}')
                continue

    return wrapper


def is_trading_time() -> bool:
    """
    Проверяет, является ли текущее время подходящим для торговли.

    Функция определяет, является ли текущий день будним (понедельник-пятница)
    и находится ли текущее время в диапазоне с 07:00 до 23:00.

    Returns:
        bool: True, если сейчас будний день и время для торговли,
              иначе False.
    """

    current_time: datetime.datetime = datetime.datetime.now()
    is_weekday: bool = current_time.weekday() < 5
    is_within_hours: bool = 7 <= current_time.hour < 23
    return is_weekday and is_within_hours


def repeat_trading_with_time_interval_decorator(**time_interval_kwargs):
    """
    Декоратор для повторного выполнения функции торговли с указанным интервалом
    времени, но только в рабочие часы.

    Декоратор проверяет, является ли текущее время подходящим для торговли
    (будний день и время с 07:00 до 23:00). Если текущее время не соответствует
    рабочим часам, выводит сообщение и ждет, прежде чем повторить выполнение функции.

    Параметры:
        minutes (int): Интервал времени в минутах между повторными вызовами
                       функции торговли.

    Возвращает:
        Callable: Обернутая функция, которая будет выполняться в рабочие часы
                  с заданным интервалом времени.
    """

    def trading_only_in_working_time_decorator(func):

        def wrapper(*args, **kwargs):
            while True:
                if is_trading_time():
                    func(*args, **kwargs)
                    time.sleep(datetime.timedelta(**time_interval_kwargs).total_seconds())
                    continue
                else:
                    print("Wait for stock market open...")
                    time.sleep(datetime.timedelta(**time_interval_kwargs).total_seconds())
                    continue

        return wrapper

    return trading_only_in_working_time_decorator


def loging_kwargs_decorator(func):
    """
    Декоратор для логирования вызова функции с отображением переданных позиционных и именованных аргументов.

    При вызове обёрнутой функции в лог записывается её имя, а также значения args и kwargs.

    Args:
        func (callable): функция, которую необходимо обернуть.

    Returns:
        callable: обёрнутая функция с логированием вызова.
    """
    def wrapper(*args, **kwargs):
        logging.info(f'{func.__name__}({args}, {kwargs})')
        return func(*args, **kwargs)
    return wrapper


def truncate_file_if_too_long(file_name: str, max_lines: int = 1000) -> None:
    """
    Контролирует размер файла по количеству строк и при превышении лимита
    удаляет первую половину строк, оставляя вторую.

    Args:
        file_name (str): путь к файлу для проверки и обрезки.
        max_lines (int): максимальное допустимое количество строк в файле.

    Returns:
        None
    """
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    if len(lines) > max_lines:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.writelines(lines[len(lines)//2:])