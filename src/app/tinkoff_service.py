import datetime
import functools
from decimal import Decimal
from pprint import pprint

from pandas import DataFrame
from tinkoff.invest import Account, PortfolioResponse, PositionsResponse, GetOrdersResponse, OperationsResponse
from tinkoff.invest import Client, SecurityTradingStatus, MoneyValue
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import OrderDirection, OrderType
from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation


class TkBroker:

    def __init__(self, tok: str, target: str):
        assert target in (INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX)
        self.token: str = tok
        self.target: str = target
        self.shares_df: DataFrame = get_instruments_df(self.token)


    # @property
    # def money


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


@functools.lru_cache
def get_account(token: str, target: str = INVEST_GRPC_API) -> Account:
    with Client(token=token, target=target) as client:
        account, *_ = client.users.get_accounts().accounts
        return account


def get_portfolio(token: str, target: str = INVEST_GRPC_API) -> PortfolioResponse:
    with Client(token=token, target=target) as client:
        return client.operations.get_portfolio(account_id=get_account(token, target).id)


def get_positions(token: str,  target: str = INVEST_GRPC_API) -> PositionsResponse:
    with Client(token=token, target=target) as client:
        return client.operations.get_positions(account_id=get_account(token, target).id)


def get_orders(token: str, target: str = INVEST_GRPC_API) -> GetOrdersResponse:
    with Client(token=token, target=target) as client:
        return client.orders.get_orders(account_id=get_account(token, target).id)


def byu(figi: str, token: str, target: str = INVEST_GRPC_API):
    with Client(token=token, target=target) as client:
        sc = client.orders.post_order(
            figi=figi,
            quantity=1,
            direction=OrderDirection.ORDER_DIRECTION_BUY,
            account_id=get_account(token, target).id,
            order_type=OrderType.ORDER_TYPE_MARKET,
        )
        print(f"Return {sc}")


def sell(figi: str, token: str, target: str = INVEST_GRPC_API):
    with Client(token=token, target=target) as client:
        client.orders.post_order(
            figi=figi,
            quantity=1,
            direction=OrderDirection.ORDER_DIRECTION_SELL,
            account_id=get_account(token, target).id,
            order_type=OrderType.ORDER_TYPE_MARKET,
        )


def get_operations(token: str, target: str = INVEST_GRPC_API) -> OperationsResponse:
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


if __name__ == "__main__":
    pass

