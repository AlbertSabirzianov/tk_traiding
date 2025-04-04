import datetime
import functools
import warnings
from decimal import Decimal

import numpy
from pandas import DataFrame
from tinkoff.invest import (Account, PortfolioResponse, PositionsResponse, GetOrdersResponse,
                            OperationsResponse, PostOrderResponse, PostStopOrderResponse)
from tinkoff.invest import Client, SecurityTradingStatus, MoneyValue
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import OrderDirection, OrderType, StopOrderType, StopOrderDirection, StopOrderExpirationType, GetStopOrdersResponse
from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation, money_to_decimal

from .exceptions import TickerNotExists, NotFreeCacheForTrading


class TkBroker:
    """
    Класс для работы с брокерскими операциями через API Тинькофф.

    Атрибуты:
        token (str): Токен для авторизации в API.
        target (str): Целевая среда API (основная или песочница).
        shares_df (DataFrame): Данные о доступных инструментах (акциях).
    """

    def __init__(self, tok: str, target: str = INVEST_GRPC_API):
        assert target in (INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX)
        self.token: str = tok
        self.target: str = target
        self.shares_df: DataFrame = get_instruments_df(self.token)

    @property
    def free_money_for_trading(self) -> Decimal:
        """
        Рассчитывает сумму свободных средств, доступных для торговли.

        Это свойство получает текущий денежный баланс и корректирует его на основе
        стоимости коротких позиций в портфеле. Расчёт включает в себя:

        1. Получение общего доступного наличного остатка из позиций пользователя.
        2. Извлечение деталей портфеля для оценки любых коротких позиций.
        3. Расчёт общей стоимости коротких позиций путём умножения
           текущей цены активов на количество, находящееся в короткой продаже.
        4. Удвоение стоимости коротких позиций для учёта потенциальных
           требований по марже.

        Возвращает:
            Decimal: Общая сумма свободных средств, доступных для торговли,
            которая включает в себя денежный баланс и скорректированную стоимость
            коротких позиций.
        """
        positions: PositionsResponse = get_positions(token=self.token, target=self.target)
        if not positions.money:
            return Decimal(0)
        money: Decimal = money_to_decimal(positions.money[0])

        portfolio: PortfolioResponse = get_portfolio(self.token, self.target)
        shorts_money: Decimal = Decimal(0)
        for portfolio_position in portfolio.positions:
            quantity: Decimal = quotation_to_decimal(portfolio_position.quantity)
            if quantity < 0:
                current_p: Decimal = money_to_decimal(portfolio_position.current_price)
                shorts_money += current_p * quantity
        return money + (shorts_money * 2)

    def get_last_price_for_lot(self, figi: str) -> Decimal:
        """
        Получает последнюю цену за лот по FIGI.

        Аргументы:
            figi (str): FIGI инструмента.

        Возвращает:
            Decimal: Последняя цена за лот.
        """
        last_price: Decimal = get_last_price(token=self.token, target=self.target, figi=figi)
        lot: numpy.int64 = self.shares_df[self.shares_df["figi"] == figi]["lot"].iloc[0]
        return last_price * Decimal(int(lot))

    def get_figi_by_ticker(self, ticker: str) -> str:
        """
        Получает FIGI инструмента по его тикеру.

        Аргументы:
            ticker (str): Тикер инструмента.

        Возвращает:
            str: FIGI инструмента.

        Исключения:
            TickerNotExists: Если тикер не существует.
        """
        if self.shares_df[self.shares_df["ticker"] == ticker].empty:
            raise TickerNotExists
        return self.shares_df[self.shares_df["ticker"] == ticker]["figi"].iloc[0]

    def validate_tickers(self, stock_tickers: list[str]) -> list[str]:
        """
        Проверяет список тикеров на существование.

        Аргументы:
            stock_tickers (list[str]): Список тикеров для проверки.

        Возвращает:
            list[str]: Список валидных тикеров.
        """
        validated_tickers: list[str] = []
        for ticker in stock_tickers:
            try:
                self.get_figi_by_ticker(ticker)
                validated_tickers.append(ticker)
            except TickerNotExists:
                warnings.warn(f"Ticker {ticker} Not Exists!")
                continue
        return validated_tickers

    def post_short_position(self, ticker: str, take_profit_percent: float, stop_loss_percent: float):
        """
        Открывает короткую позицию с заданными параметрами.

        Аргументы:
            ticker (str): Тикер инструмента.
            take_profit_percent (float): Процент прибыли для фиксации.
            stop_loss_percent (float): Процент убытка для фиксации.

        Исключения:
            NotFreeCacheForTrading: Если недостаточно средств для торговли.
        """
        figi: str = self.get_figi_by_ticker(ticker)
        last_price_for_lot: Decimal = self.get_last_price_for_lot(figi)
        if self.free_money_for_trading <= (last_price_for_lot * Decimal(1.01)):
            raise NotFreeCacheForTrading

        sell_order: PostOrderResponse = sell_market(figi, self.token, self.target)
        current_price: Decimal = money_to_decimal(sell_order.executed_order_price)

        take_profit_price: Decimal = current_price - current_price * Decimal(take_profit_percent / 100)
        stop_loss_price: Decimal = current_price + current_price * Decimal(stop_loss_percent / 100)

        min_price_increment: Decimal = self.shares_df[
            self.shares_df["figi"] == figi
        ]["min_price_increment"].iloc[0]

        post_buy_take_profit(
            token=self.token,
            target=self.target,
            figi=figi,
            price=Decimal(round(take_profit_price / min_price_increment) * min_price_increment)
        )
        post_buy_stop_loss(
            token=self.token,
            target=self.target,
            figi=figi,
            price=Decimal(round(stop_loss_price / min_price_increment) * min_price_increment)
        )

    def post_long_position(self, ticker: str, take_profit_percent: float, stop_loss_percent: float):
        """
        Открывает длинную позицию с заданными параметрами.

        Аргументы:
            ticker (str): Тикер инструмента.
            take_profit_percent (float): Процент прибыли для фиксации.
            stop_loss_percent (float): Процент убытка для фиксации.

        Исключения:
            NotFreeCacheForTrading: Если недостаточно средств для торговли.
        """
        figi: str = self.get_figi_by_ticker(ticker)
        last_price_for_lot: Decimal = self.get_last_price_for_lot(figi)
        if self.free_money_for_trading <= (last_price_for_lot * Decimal(1.01)):
            raise NotFreeCacheForTrading

        byu_order: PostOrderResponse = byu_market(figi, self.token, self.target)
        current_price: Decimal = money_to_decimal(byu_order.executed_order_price)

        take_profit_price: Decimal = current_price + current_price * Decimal(take_profit_percent / 100)
        stop_loss_price: Decimal = current_price - current_price * Decimal(stop_loss_percent / 100)

        min_price_increment: Decimal = self.shares_df[
            self.shares_df["figi"] == figi
        ]["min_price_increment"].iloc[0]

        post_sell_take_profit(
            token=self.token,
            target=self.target,
            figi=figi,
            price=Decimal(round(take_profit_price / min_price_increment) * min_price_increment)
        )
        post_sell_stop_loss(
            token=self.token,
            target=self.target,
            figi=figi,
            price=Decimal(round(stop_loss_price / min_price_increment) * min_price_increment)
        )


@functools.lru_cache
def get_instruments_df(token: str) -> DataFrame:
    with Client(token=token) as client:
        tickers = []
        for item in client.instruments.shares().instruments:
            tickers.append(
                {
                    "name": item.name,
                    "ticker": item.ticker,
                    "class_code": item.class_code,
                    "figi": item.figi,
                    "uid": item.uid,
                    "type": "shares",
                    "min_price_increment": quotation_to_decimal(
                        item.min_price_increment
                    ),
                    "scale": 9 - len(str(item.min_price_increment.nano)) + 1,
                    "lot": item.lot,
                    "trading_status": str(
                        SecurityTradingStatus(item.trading_status).name
                    ),
                    "api_trade_available_flag": item.api_trade_available_flag,
                    "currency": item.currency,
                    "exchange": item.exchange,
                    "buy_available_flag": item.buy_available_flag,
                    "sell_available_flag": item.sell_available_flag,
                    "short_enabled_flag": item.short_enabled_flag,
                    "klong": quotation_to_decimal(item.klong),
                    "kshort": quotation_to_decimal(item.kshort),
                }
            )
        return DataFrame(tickers)


def get_last_price(token: str, target: str, figi: str) -> Decimal:
    with Client(token=token, target=target) as client:
        return quotation_to_decimal(
            client.market_data.get_last_prices(figi=[figi],).last_prices[0].price
        )


@functools.lru_cache
def get_account(token: str, target: str = INVEST_GRPC_API) -> Account:
    with Client(token=token, target=target) as client:
        account, *_ = client.users.get_accounts().accounts
        return account


def close_all_stop_orders(token: str, target: str = INVEST_GRPC_API):
    with Client(token=token, target=target) as client:
        stop_orders_response: GetStopOrdersResponse = client.stop_orders.get_stop_orders(
            account_id=get_account(token, target).id
        )
        for stop_order in stop_orders_response.stop_orders:
            client.stop_orders.cancel_stop_order(
                account_id=get_account(token, target).id,
                stop_order_id=stop_order.stop_order_id
            )


def get_portfolio(token: str, target: str = INVEST_GRPC_API) -> PortfolioResponse:
    with Client(token=token, target=target) as client:
        return client.operations.get_portfolio(account_id=get_account(token, target).id)


def get_positions(token: str,  target: str = INVEST_GRPC_API) -> PositionsResponse:
    with Client(token=token, target=target) as client:
        return client.operations.get_positions(account_id=get_account(token, target).id)


def get_orders(token: str, target: str = INVEST_GRPC_API) -> GetOrdersResponse:
    with Client(token=token, target=target) as client:
        return client.orders.get_orders(account_id=get_account(token, target).id)


def byu_market(figi: str, token: str, target: str = INVEST_GRPC_API) -> PostOrderResponse:
    with Client(token=token, target=target) as client:
        return client.orders.post_order(
            figi=figi,
            quantity=1,
            direction=OrderDirection.ORDER_DIRECTION_BUY,
            account_id=get_account(token, target).id,
            order_type=OrderType.ORDER_TYPE_MARKET,
        )


def sell_market(figi: str, token: str, target: str = INVEST_GRPC_API) -> PostOrderResponse:
    with Client(token=token, target=target) as client:
        return client.orders.post_order(
            figi=figi,
            quantity=1,
            direction=OrderDirection.ORDER_DIRECTION_SELL,
            account_id=get_account(token, target).id,
            order_type=OrderType.ORDER_TYPE_MARKET,
        )


def post_buy_take_profit(token: str, target: str, figi: str, price: Decimal) -> PostStopOrderResponse:
    with Client(token=token, target=target) as client:
        return client.stop_orders.post_stop_order(
            figi=figi,
            quantity=1,
            price=decimal_to_quotation(price),
            stop_price=decimal_to_quotation(price),
            account_id=get_account(token=token, target=target).id,
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT
        )


def post_sell_take_profit(token: str, target: str, figi: str, price: Decimal) -> PostStopOrderResponse:
    with Client(token=token, target=target) as client:
        return client.stop_orders.post_stop_order(
            figi=figi,
            quantity=1,
            price=decimal_to_quotation(price),
            stop_price=decimal_to_quotation(price),
            account_id=get_account(token=token, target=target).id,
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT
        )


def post_buy_stop_loss(token: str, target: str, figi: str, price: Decimal) -> PostStopOrderResponse:
    with Client(token=token, target=target) as client:
        return client.stop_orders.post_stop_order(
            figi=figi,
            quantity=1,
            price=decimal_to_quotation(price),
            stop_price=decimal_to_quotation(price),
            account_id=get_account(token=token, target=target).id,
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS
        )


def post_sell_stop_loss(token: str, target: str, figi: str, price: Decimal) -> PostStopOrderResponse:
    with Client(token=token, target=target) as client:
        return client.stop_orders.post_stop_order(
            figi=figi,
            quantity=1,
            price=decimal_to_quotation(price),
            stop_price=decimal_to_quotation(price),
            account_id=get_account(token=token, target=target).id,
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS
        )


def get_today_operations(token: str, target: str) -> OperationsResponse:
    with Client(token=token, target=target) as client:
        return client.operations.get_operations(
            account_id=get_account(token, target).id,
            from_=datetime.datetime.now().replace(hour=0, minute=0, second=0),
            to=datetime.datetime.now()
        )


def add_money_sandbox(token: str, money: float):
    with Client(token=token, target=INVEST_GRPC_API_SANDBOX) as client:
        money = decimal_to_quotation(Decimal(money))
        client.sandbox.sandbox_pay_in(
            account_id=get_account(token, INVEST_GRPC_API_SANDBOX).id,
            amount=MoneyValue(units=money.units, nano=money.nano, currency="rub")
        )
