class NotFreeCacheForTrading(Exception):
    """Исключение, возникающее, когда кэш для торговли закончился или недоступен."""
    pass


class TickerNotExists(Exception):
    """Исключение, возникающее, когда запрашиваемый тикер не существует в системе."""
    pass
