import statsmodels.tsa.stattools as ts
import talib

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
        self.volatility = tick["volatility"]
        self.adx = tick["adx"]
        self.adf_1 = tick["ADF_1"]
        self.adf_5 = tick["ADF_5"]
        self.adf_10 = tick["ADF_10"]
        self.adf_p = tick["ADF_p"]
        self.adf_stat = tick["ADF_stat"]
        self.cum_ret = tick["cum_ret"]*10000

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
	    	self._time, self.symbol, self.closeBid, self.closeAsk,
                self.K, self.D, self.sma, self.ewma, self.upper, self.lower)

    def write_tick(self):
        with open(self.path, "a") as file:
            file.write(self.__str__())


class Compute(GetCandles):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity):
        GetCandles.__init__(self, account, count, symbol, granularity)
        self.candles = self.request()
        self._open = self.candles["openMid"].values
        self.high = self.candles["highMid"].values
        self.low = self.candles["lowMid"].values
        self.close = self.candles["closeMid"].values
        self.longWin = longWin
        self.shortWin = shortWin
        self.candles["total_volume"] = self.candles["volume"].sum()
        self.stoch_osc()
        self.adf_test()
        self.cum_ret()
        self.moving_average()
        self.bbands()
        self.adx()
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
        self.candles["K"], self.candles["D"] = talib.STOCH(self.high, 
                                                           self.low, 
                                                           self.close,
                                                           slowk_period=52,
                                                           fastk_period=68,
                                                           slowd_period=52)

    def moving_average(self):
        self.candles["sma"] = talib.SMA(self.close, timeperiod=self.shortWin)
        self.candles["ewma"] = talib.EMA(self.close, timeperiod=self.shortWin)

    def macd(self):
        self.candles["macd"], self.candles["macd_sig"], self.candles["macd_hist"] = talib.MACD(self.close)

    def bbands(self):
        self.candles["upper_band"], self.candles["mid"], self.candles["lower_band"] = talib.BBANDS(self.close, timeperiod=self.longWin)
        self.candles["volatility"] = (self.candles["upper_band"] - self.candles["lower_band"])*10000

    def cum_ret(self):
        self.candles["cum_ret"] = self.candles["closeMid"].pct_change().cumsum()

    def adx(self):
        self.candles["adx"] = talib.ADX(self.high, self.low, self.close, timeperiod=48)


class Signals(Compute):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity="S5"):
        Compute.__init__(self, account, count, symbol, longWin, shortWin, granularity)
        self.channel, self.stoch = self.stoch_signals()
        self.bbands_channel = self.bband_signals()
        self.mavg_state = self.moving_avg_signals()

    def stoch_signals(self):
        K, D = self.tick.K, self.tick.D
        if 80 < K < 90:
            channel = 1
        elif 10 < K < 20:
            channel = -1
        else:
            channel = 0
        if K > D:
            stoch = 1
        elif K < D:
            stoch = -1
        return channel, stoch

    def bband_signals(self):
        upper, lower, closeMid = self.tick.upper, self.tick.lower, self.tick.closeMid
        if lower < closeMid < upper:
            channel = 0
        elif closeMid > upper:
            channel = 1
        elif closeMid < lower:
            channel = -1
        return channel

    def moving_avg_signals(self):
        sma, ewma = self.tick.sma, self.tick.ewma
        if ewma > sma:
            sma_state = 1
        elif ewma < sma:
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
