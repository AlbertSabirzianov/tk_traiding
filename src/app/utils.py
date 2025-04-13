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
