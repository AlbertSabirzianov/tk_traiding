class NotFreeCacheForTrading(Exception):
    """Исключение, возникающее, когда кэш для торговли закончился или недоступен."""
    pass


class TickerNotExists(Exception):
    """Исключение, возникающее, когда запрашиваемый тикер не существует в системе."""
    pass


class ShortPositionNotAvailable(Exception):
    """Исключение, возникающее, когда short позиция не доступна."""
    pass


class LongPositionNotAvailable(Exception):
    """Исключение, возникающее, когда long позиция не доступна."""
    pass