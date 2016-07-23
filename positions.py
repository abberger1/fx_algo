import datetime as dt
import requests
import numpy as np

from config import LoggingPaths
from account import Account

class PnL:
    def __init__(self, tick, position):
        self.tick = tick
        self.position = position

    def get_pnl(self):
        if self.position.side == "short":
            pnl = (self.position.price - self.tick.closeAsk)*self.position.units
        elif self.position.side == "long":
            pnl = (self.tick.closeBid - self.position.price)*self.position.units
        return pnl

class MostRecentPosition:
    def __init__(self, side, price, units):
        self.side = side
        self.price = price
        self.units = units

        self.order = [self.side, self.units, self.price]

    def __repr__(self):
        return "SIDE: %s PRICE: %s UNITS: %s\n" % (
                self.side, np.mean(self.price), self.units)

class Positions(Account):
    def _checkPosition(self, symbol):
        try:
                url = self.position_url() + symbol
                params = {'instruments': symbol,
                           "accountId": self.id}
                req = requests.get(url, headers=self.get_headers(),
                                                   data=params).json()
        except Exception as e:
                print(">>> Caught exception returning position\n%s\n%s"%(
                                    str(e), req))
                return False

        if "code" in req:
                #print(req)
                return False

        elif 'side' in req:
                _side = req['side']
                units = req['units']
                price = req['avgPrice']

                if _side == 'sell': side = 'short'
                elif _side == 'buy': side = 'long'

                position = {'side': side,
                        'units': units,
                        'price': price}
                return position
        else:
                print(req)
                return False

    def checkPosition(self, symbol):
        position = self._checkPosition(symbol)
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
        self.id = ("|").join([str(x) for x in position["ids"]])
        self.instrument = position["instrument"]
        self.price = position["price"]
        self.units = position["units"]

        self.profit_loss = profit_loss
        self.side = side
        self.tick = tick

        self.path = LoggingPaths.trades

    def __str__(self):
        return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%(
        self._time, self.id, self.side,self.profit_loss, self.units, self.price,
        self.tick.K, self.tick.D, self.tick.cum_ret,self.tick.closeAsk, self.tick.closeBid,         self.tick.volume,self.tick.adf_p, self.tick.adf_stat)

    def write_exit(self):
        with open(self.path, "a") as file:
                file.write(self.__str__())

class ExitPosition(Account):
    def __init__(self):
        super().__init__()
        self.url = self.position_url() + self.symbol
        self.headers = self.get_headers()

    def _closePosition(self, symbol):
        try:
            req = requests.delete(self.url, headers=self.headers).json()
        except Exception as e:
            print('Unable to delete positions: \n', str(e))
            return req
        try:
            ids = req['ids']
            instrument = req['instrument']
            units = req['totalUnits']
            price = req['price']
            orderData = {'ids': ids, 'instrument': instrument,
                            'units': units, 'price': price}
            return orderData
        except Exception as e:
            print('Caught exception closing positions: \n%s\n%s'%(str(e), req))
            return False

    def closePosition(self, position, profit_loss, tick):
        exit = self._closePosition("EUR_USD")
        if exit["units"] != 0:
            exit = MostRecentExit(exit, position.side, profit_loss, tick)
            exit.write_exit()
            return exit
        else:
            print(">>> No positions removed\n(%s)"%position)
            return False
