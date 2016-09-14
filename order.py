import json
import requests
import pandas as pd
import datetime as dt

from config import LoggingPaths
from account import Account

class MostRecentReject(Account):
    def __init__(self, order, params):
        super().__init__()

        self._time = dt.datetime.now().timestamp()
        self.code = order["code"]
        self.message = order["message"]
        self.params = params

        self.reject = True # will not log

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # code == 23
        return "EVENT:REJECT TIME:%s %s PRICE: %s MSG:%s" % (
                            self._time, self.params['side'], self.params['price'], self.message)

class MostRecentTrade:
    """
    Market Orders --> response from Oanda POST
    Receives and handles the order data
    """
    def __init__(self, order, tick):
        self.order = order
        self.tick = tick
        self.path = LoggingPaths.trades

        self.closed = self.closed_trade()
        self.opened = self.opened_trade()

        self.reject = False

    def closed_trade(self):
        if ("tradesClosed" in self.order) and self.order["tradesClosed"]:
            self.time = dt.datetime.strptime(self.order["time"],
                           "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

            try:
                self.side = self.order["tradesClosed"][0]["side"]
                self.id = self.order["tradesClosed"][0]["id"]
                self.units = self.order["tradesClosed"][0]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                #self.mktSnapshot()
                return True
            except KeyError as e:
                print("Caught exception in closed_trade\n%s"%e)
        else:
            pass

    def opened_trade(self):
        if ("tradeOpened" in self.order) and self.order["tradeOpened"]:
            self.time = dt.datetime.strptime(self.order["time"],
                           "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            try:
                self.side = self.order["tradeOpened"]["side"]
                self.id = self.order["tradeOpened"]["id"]
                self.units = self.order["tradeOpened"]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                #self.mktSnapshot()
                return True
            except KeyError as e:
                print(self.order)
                print("Caught exception in opened_trade\n%s"%e)
        else:
            pass

    def __repr__(self):
        return str(self.order)

    def __str__(self):
        return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%(
            self.time,self.id,self.side,self.instrument,self.units,self.price,
            self.tick.adf_p,self.tick.adf_stat,self.tick.K, self.tick.D,
            self.tick.cum_ret, self.tick.closeAsk, self.tick.closeBid,self.tick.volume)

    def mktSnapshot(self):
        with open(self.path, "a") as file:
            file.write(self.__str__())

class MostRecentOrder(Account):
    """
    Limit Orders --> response from Oanda POST
    """
    def __init__(self, order, tick):
        super().__init__()
        self.url = self.order_url()
        self.headers = self.get_headers()

        self._time = dt.datetime.now().timestamp()
        self.price = order["price"]
        self.instrument = order["instrument"]
        self.side = order["orderOpened"]["side"]
        self.id = order["orderOpened"]["id"]
        self.units = order["orderOpened"]["units"]
        self.expiry = order["orderOpened"]["expiry"]

        self.tick = tick
        self.path = LoggingPaths.orders

        self.reject = False

    def working(self):
        try:
                resp = requests.get(self.url, headers=self.headers, verify=False).json()
                return resp
        except Exception as e:
                raise ValueError(">>> Caught exception retrieving orders: %s"%e)

    def delete(self):
        try:
                resp = requests.request("DELETE", self.url,
                                        headers=self.headers, verify=False).json()
                return resp
        except Exception as e:
                raise ValueError(">>> Caught exception retrieving orders: %s"%e)

    def __str__(self):
        return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%(
            self._time,self.id,self.side,self.instrument,self.units,self.price,
            self.tick.volume,self.tick.volatility,
            self.tick.K, self.tick.closeAsk,
            self.tick.closeBid, self.tick.total_volume)

    def mktSnapshot(self):
        with open(self.path, "a") as file:
            file.write(self.__str__())

class OrderHandler(Account):
    def __init__(self, symbol, tick, side, quantity,
                            kind="market", price=0):
        super().__init__()
        self.url = self.order_url()
        self.headers = self.get_headers()

        self.side = side
        self.quantity = quantity

        self.tick = tick

        self.symbol = symbol
        self.side = side
        self.quantity = quantity

        self.kind = kind
        self.price = price

        self.expiry = str(int((dt.datetime.utcnow().timestamp())))

    def execute_price(self):
        if self.side == "buy":
                _price = self.tick.closeBid - 0.0001
        elif self.side == "sell":
                _price = self.tick.closeAsk + 0.0001
        else:
            raise NotImplementedError(
                   ">>> Invalid side !! \n>>> Order not complete.")
        return _price

    def market_order(self):
        _price = self.execute_price()
        params = {'instrument': self.symbol,
                  'side': self.side,
                  'type': self.kind,
                  'units': self.quantity,
                  "price": _price,
                  "upperBound": _price+0.00005,
                  "lowerBound": _price-0.00005}
        return params

    def limit_order(self):
        self.headers["X-Accept-Datetime-Format"] = "UNIX"
        params = {'instrument': self.symbol,
                  'side': self.side,
                  'type': self.kind,
                  'units': self.quantity,
                  "price": self.price,
                 "expiry": self.expiry}
        return params

    def _send_order(self):
        if self.kind == "limit":
                params = self.limit_order()
        elif self.kind == "market":
                params = self.market_order()
        else:
                raise NotImplementedError(
                ">>> Invalid order type %s, exiting. TRADE NOT DONE" % self.kind)

        try:
                resp = requests.post(self.url, headers=self.headers,
                                                 data=params, verify=False).json()
                return resp, params
        except Exception as e:
                print(">>> Caught exception sending order\n%s"%(e))
                return False

    def send_order(self):
        order, price = self._send_order()
        if order:
                # market order
                if "tradeOpened" in order.keys():
                        order = MostRecentTrade(order, self.tick)
                # limit order
                elif "orderOpened" in order.keys():
                        order = MostRecentOrder(order, self.tick)
                        #order.mktSnapshot()
                # reject
                elif "code" in order.keys():
                        if order["code"] == 23 or order["code"] == 22:
                                order = MostRecentReject(order, price)
                                print(order)
                        else:
                            raise NotImplementedError(
                            "order[\'code\'] not an integer or != 23 or 22")
                return order
        else:
                print(ValueError(
                "%s>>> Order not complete\n"%order))
                return False


if __name__ == '__main__':
    from sys import argv
    from signals import Signals
    from positions import Positions

    if len(argv) < 4:
        raise ValueError('Usage: order.py side quantity product')

    tick = Signals(1250, argv[3], 900, 450).tick
    order = OrderHandler(argv[3], tick, argv[1], argv[2]).send_order()
    position = Positions().checkPosition(argv[3])

    print(position)
    print(tick)
