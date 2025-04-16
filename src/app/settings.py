from pydantic_settings import BaseSettings


class TradingViewSettings(BaseSettings):
    """
    Настройки конфигурации для TradingView.

    Атрибуты:
        exchange (str): Биржа, которую следует использовать. По умолчанию "RUS".
        screener (str): Скринер, который следует использовать. По умолчанию "russia".
    """
    exchange: str = "RUS"
    screener: str = "russia"


class StrategySettings(BaseSettings):
    """
    Настройки конфигурации для торговых стратегий.

    Атрибуты:
        profit_percent (float): Целевая процентная прибыль для стратегии.
        stopp_loss_percent (float): Процент стоп-лосса для стратегии.
        stocks (list[str]): Список символов акций, на которые будет применяться стратегия.
    """
    profit_percent: float
    stopp_loss_percent: float
    stocks: list[str]


class TinkoffSettings(BaseSettings):
    """
    Настройки конфигурации для интеграции с API Тинькофф.

    Атрибуты:
        tk_api_key (str): API-ключ для доступа к сервисам Тинькофф.
    """
    tk_api_key: str


class TelegramSettings(BaseSettings):
    """
    Настройки телеграм бота для отправки уведомлений.

    Атрибуты:
        bot_token (str): токен телеграм бота.
        chanel_name (str): имя телеграм канала, куда будет присылаться информация.
    """

    bot_token: str
    chanel_name: str
