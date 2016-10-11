import statsmodels.tsa.stattools as ts
from prices import StreamPrices, GetCandles
from config import Paths
from position import Positions
from account import Account


class Tick(object):
    def __init__(self, tick):
        self.symbol = tick["symbol"]
        self.path = Paths(self.symbol).ticks
        self._time = tick["timestamp"]
        self.closeBid = tick["closeBid"]
        self.closeAsk = tick["closeAsk"]
        self.spread = self.closeAsk - self.closeBid
        self.openMid = tick["openMid"]
        self.highMid = tick["highMid"]
        self.lowMid = tick["lowMid"]
        self.closeMid = tick["closeMid"]
        self.K = tick['K']
        self.D = tick['D']
        self.volume = tick["volume"]
        self.total_volume = tick["total_volume"]
        self.sma = tick["sma"]
        self.ewma = tick["ewma"]
        self.upper = tick["upper_band"]
        self.lower = tick["lower_band"]
        self.adf_1 = tick["ADF_1"]
        self.adf_5 = tick["ADF_5"]
        self.adf_10 = tick["ADF_10"]
        self.adf_p = tick["ADF_p"]
        self.adf_stat = tick["ADF_stat"]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "%s,%s,%s,%s" % (
                self._time, self.symbol, self.closeBid, self.closeAsk)

    def write_tick(self):
        with open(self.path, "a") as file:
            file.write(self.__str__())


class Compute(GetCandles):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity):
        GetCandles.__init__(self, account, count, symbol, granularity)
        self.candles = self.request()
        self.longWin = longWin
        self.shortWin = shortWin
        self._open = self.candles["openMid"]
        self.high = self.candles["highMid"]
        self.low = self.candles["lowMid"]
        self.close = self.candles["closeMid"]
        self.candles["total_volume"] = self.candles["volume"].sum()
        self.moving_average()
        self.stoch_osc()
        self.adf_test()
        self.bbands()
        self.tick = Tick(self.candles.ix[self.candles.index[-1]])

    def adf_test(self):
        test = ts.adfuller(self.candles["closeMid"], maxlag=1)
        adf_crit = test[4]
        self.candles["ADF_1"] = adf_crit["1%"]
        self.candles["ADF_5"] = adf_crit["5%"]
        self.candles["ADF_10"] = adf_crit["10%"]
        self.candles["ADF_p"] = test[1]
        self.candles["ADF_stat"] = test[0]

    def stoch_osc(self):
        self.candles['max'] = self.high.rolling(window=self.longWin).max()
        self.candles['min'] = self.low.rolling(window=self.longWin).min()
        
        self.candles['K'] = (self.close - self.candles['min']) / (self.candles['max'] - self.candles['min']) * 100
        self.candles['D'] = self.candles['K'].rolling(window=3).mean()

    def moving_average(self):
        self.candles['sma'] = self.close.rolling(window=self.longWin).mean()
        self.candles['ewma'] = self.close.rolling(window=self.shortWin).mean()

    def bbands(self):
        self.candles['upper_band'] = self.candles['sma'] + self.close.rolling(window=self.longWin).std() * 2
        self.candles['lower_band'] = self.candles['sma'] - self.close.rolling(window=self.longWin).std() * 2


class Signals(Compute):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity="S5"):
        Compute.__init__(self, account, count, symbol, longWin, shortWin, granularity)
        self.channel, self.stoch = self.stoch_signals()
        self.bbands_channel = self.bband_signals()
        self.mavg_state = self.moving_avg_signals()

    def stoch_signals(self):
        if 80 < self.tick.K < 90:
            channel = 1
        elif 10 < self.tick.K < 20:
            channel = -1
        else:
            channel = 0
        if self.tick.K > self.tick.D:
            stoch = 1
        elif self.tick.K < self.tick.D:
            stoch = -1
        return channel, stoch

    def bband_signals(self):
        if self.tick.lower < self.tick.closeMid < self.tick.upper:
            channel = 0
        elif self.tick.closeMid > self.tick.upper:
            channel = 1
        elif self.tick.closeMid < self.tick.lower:
            channel = -1
        return channel

    def moving_avg_signals(self):
        if self.tick.ewma > self.tick.sma:
            sma_state = 1
        elif self.tick.ewma < self.tick.sma:
            sma_state = -1
        return sma_state


if __name__ == '__main__':
    from sys import argv

    if len(argv) > 1:
        symbol = argv[1]
        account = Account()
        tick = Signals(account, 1250, symbol, 900, 450).tick
        #order = OrderHandler(argv[3], tick, symbol, argv[2]).send_order()
        position = Positions(account, symbol).checkPosition()

        print(position)
        print(tick)