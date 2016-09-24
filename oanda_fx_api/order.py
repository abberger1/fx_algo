import requests
import datetime as dt
from config import Paths


class MostRecentOrder:
    """
    Limit Orders --> response from Oanda POST
    """
    def __init__(self, account, order, tick):
        self.account = account
        self._time = dt.datetime.now().timestamp()
        self.price = order["price"]
        self.instrument = order["instrument"]
        self.side = order["orderOpened"]["side"]
        self.id = order["orderOpened"]["id"]
        self.units = order["orderOpened"]["units"]
        self.expiry = order["orderOpened"]["expiry"]
        self.tick = tick
        self.path = Paths.orders
        self.reject = False

    def working(self):
        try:
            resp = requests.get(self.url, headers=self.headers, verify=False).json()
            return resp
        except Exception as e:
            raise ValueError(">>> Caught exception retrieving orders: %s"%e)

    def delete(self):
        try:
            resp = requests.request("DELETE", self.url, headers=self.headers, verify=False).json()
            return resp
        except Exception as e:
                raise ValueError(">>> Caught exception retrieving orders: %s"%e)


class MostRecentReject:
    def __init__(self, order, params):
        self._time = dt.datetime.now().timestamp()
        self.code = order["code"]
        self.message = order["message"]
        self.params = params
        self.reject = True # will not log

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # code == 23
        return "[=> REJECT %s %s @ %s (%s)" % (
                self._time, self.params['side'], self.params['price'], self.message)


class MostRecentTrade:
    """
    Market Orders --> response from Oanda POST
    Receives and handles the order data
    """
    def __init__(self, order, tick):
        self.order = order
        self.tick = tick
        self.path = Paths.trades
        self.trade = self._trade()
        self.reject = False

    def _trade(self):
        if "tradesClosed" in self.order and self.order["tradesClosed"]:
            self.time = dt.datetime.strptime(self.order["time"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            try:
                self.side = self.order["tradesClosed"][0]["side"]
                self.id = self.order["tradesClosed"][0]["id"]
                self.units = self.order["tradesClosed"][0]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                return True
            except KeyError as e:
                print("Caught exception in closed_trade\n%s"%e)

        elif "tradeOpened" in self.order and self.order["tradeOpened"]:
            self.time = dt.datetime.strptime(self.order["time"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            try:
                self.side = self.order["tradeOpened"]["side"]
                self.id = self.order["tradeOpened"]["id"]
                self.units = self.order["tradeOpened"]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                return True
            except KeyError as e:
                print("Caught exception in opened_trade\n%s"%e)
        return False

    def __repr__(self):
        return str(self.order)


class OrderHandler:
    def __init__(self, account, symbol, tick, side, quantity, kind="market", price=0):
        self.account = account
        self.url = account.orders
        self.headers = self.account.headers
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
            return self.tick.closeBid - 0.0001
        elif self.side == "sell":
            return self.tick.closeAsk + 0.0001
        else:
            raise NotImplementedError("Invalid side. Order not done.")

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
        params = self.market_order() if self.kind == 'market' else self.limit_order()
        try:
            resp = requests.post(self.url, headers=self.headers, data=params, verify=False).json()
        except Exception as e:
            print(">>> Caught exception sending order\n%s" % e)
            return False
        return resp, params

    def send_order(self):
        order, params = self._send_order()
        if order:
            if "tradeOpened" in order.keys():
                order = MostRecentTrade(order, self.tick)
            elif "orderOpened" in order.keys():
                order = MostRecentOrder(order, self.tick)
            elif "code" in order.keys():
                if order["code"] == 23 or order["code"] == 22:
                    order = MostRecentReject(order, params)
                    print(order)
                else:
                    raise NotImplementedError("order[\'code\'] not an integer or != 23 or 22")
            return order
        else:
            print("%s Order not done\n" % order)
            return False
