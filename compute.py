#import talib
import statsmodels.tsa.stattools as ts

from tick import Tick
from account import Account
from req_prices import GetCandles


class Compute(Account):
    def __init__(self, count, symbol, longWin, shortWin, granularity):
        super().__init__()

        self.candles = GetCandles(count, symbol, granularity).request()

        self._open = self.candles["openMid"].values
        self.high = self.candles["highMid"].values
        self.low = self.candles["lowMid"].values
        self.close = self.candles["closeMid"].values

        self.longWin = longWin
        self.shortWin = shortWin

#	self.candles["total_volume"] = self.candles["volume"].sum()

#        self.stoch_osc()
#        self.adf_test()
#        self.cum_ret()
#
#        self.moving_average()
#        self.bbands()
#        self.adx()
#
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
        self.candles["K"], self.candles["D"] = talib.STOCH(self.high, self.low, self.close,
                                                            slowk_period=52,
                                                            fastk_period=68,
                                                            slowd_period=52)
        self.candles["momentum"] = self.candles["K"].rolling(center=False,
                                                             window=self.shortWin).mean() - 50

    def moving_average(self):
        self.candles["sma"] = talib.SMA(self.close,
                                        timeperiod=self.shortWin)
        self.candles["ewma"] = talib.EMA(self.close,
                                         timeperiod=self.shortWin)

    def macd(self):
        self.candles["macd"], self.candles["macd_sig"], self.candles["macd_hist"] = talib.MACD(self.close)

    def bbands(self):
        self.candles["upper_band"], self.candles["mid"], self.candles["lower_band"] = talib.BBANDS(self.close,
                                                                                                    timeperiod=self.longWin)
        self.candles["volatility"] = (self.candles["upper_band"] - self.candles["lower_band"])*10000

    def cum_ret(self):
        self.candles["cum_ret"] = self.candles["closeMid"].pct_change().cumsum()

    def adx(self):
        self.candles["adx"] = talib.ADX(self.high,
                                        self.low,
                                        self.close,
                                        timeperiod=48)
