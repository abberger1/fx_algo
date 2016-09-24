import requests
import numpy as np
from config import Paths


class PnL:
    def __init__(self, tick, position):
        self.tick = tick
        self.position = position

    def get_pnl(self):
        if self.position.side == "short":
            return (self.position.price - self.tick.closeAsk) * self.position.units
        elif self.position.side == "long":
            return (self.tick.closeBid - self.position.price) * self.position.units


class MostRecentPosition:
    def __init__(self, side, price, units):
        self.side = side
        self.price = price
        self.units = units
        self.order = [self.side, self.units, self.price]

    def __repr__(self):
        return "SIDE: %s PRICE: %s UNITS: %s\n" % (
                self.side, np.mean(self.price), self.units)


class Positions:
    def __init__(self, account, symbol):
        self.account = account
        self.headers = self.account.headers
        self.symbol = symbol
        self.url = '%s%s' % (self.account.positions, self.symbol)

    def _checkPosition(self):
        params = {'instruments': self.symbol,
                  "accountId": self.account.id}
        try:
            req = requests.get(self.url, headers=self.headers, data=params).json()
        except Exception as e:
            print(">>> Error returning position\n%s\n%s" % (str(e), req))
            return False

        if "code" in req:
            return False
        elif 'side' in req:
            side = 'short' if req['side'] == 'sell' else 'long'
            position = {'side': side,
                        'units': req['units'],
                        'price': req['avgPrice']}
        else:
            print(req)
            return False
        return position

    def checkPosition(self):
        position = self._checkPosition()
        if position:
            position = MostRecentPosition(position["side"],
                                          position["price"],
                                          position["units"])
            return position
        else:
            return MostRecentPosition(0, 0, 0)


class MostRecentExit:
    def __init__(self, position, side, profit_loss, tick):
        self._time = tick._time
        self.id = ("-").join([str(x) for x in position["ids"]])
        self.instrument = position["instrument"]
        self.price = position["price"]
        self.units = position["units"]
        self.profit_loss = profit_loss
        self.side = side
        self.tick = tick
        self.path = Paths.trades


class ExitPosition:
    def __init__(self, account):
        self.account = account
        self.url = self.position_url() + self.symbol
        self.headers = self.account.headers

    def _closePosition(self, symbol):
        try:
            req = requests.delete(self.url, headers=self.headers).json()
        except Exception as e:
            print('Unable to delete positions: \n', str(e))
            return req
        try:
            orderData = {'ids': req['ids'], 'instrument': req['instrument'],
                         'units': req['totalUnits'], 'price': req['price']}
            return orderData
        except Exception as e:
            print('Caught exception closing positions: \n%s\n%s'%(str(e), req))
            return False

    def closePosition(self, position, profit_loss, tick):
        exit = self._closePosition("EUR_USD")
        if exit["units"] != 0:
            exit = MostRecentExit(exit,
                                  position.side,
                                  profit_loss, tick)
            return exit
        else:
            print(">>> No positions removed\n(%s)"%position)
            return False
