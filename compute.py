import time
import talib
import requests
import pandas as pd
import datetime as dt
from matplotlib.dates import date2num

import statsmodels.tsa.stattools as ts

from tick import Tick
from account import Account

class GetCandles(Account):
    def __init__(self, count, symbol, granularity):
        super().__init__()
        
        self.count = count
        self.symbol = symbol
        self.granularity = granularity
        
        self.headers = {'Authorization' : 'Bearer ' + self.token}
        self.params = {'instrument' : self.symbol,
                      'granularity' : self.granularity,
                      'count' : int(self.count)}
    
    def request(self):
        try:
            req = requests.get(self.venue+"/v1/candles", headers=self.headers, 
                                                       params=self.params).json()
            candles = pd.DataFrame(req['candles'])
            candles["symbol"] = self.symbol

            candles.index = candles["time"].map(lambda x: dt.datetime.strptime(x, 
                                                          "%Y-%m-%dT%H:%M:%S.%fZ"))
            candles["timestamp"] = candles.index.map(lambda x: x.timestamp())

            candles["closeMid"] = (candles["closeAsk"]+candles["closeBid"]) / 2
            candles["lowMid"] = (candles["lowAsk"]+candles["lowBid"]) / 2
            candles["highMid"] = (candles["highAsk"]+candles["highBid"]) / 2
            candles["openMid"] = (candles["openAsk"]+candles["openBid"]) / 2
            
            return candles
        except Exception as e:
            print('%s\n>>> Error: No candles in JSON response:'%e)
            return False

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

class Signals(Compute):
    def __init__(self, count, symbol, longWin, shortWin, granularity="S5"):
        super().__init__(count, symbol, longWin, shortWin, granularity)

        self.channel, self.stoch = self.stoch_signals()
        self.bbands_channel = self.bband_signals()

        self.mavg_state = self.moving_avg_signals()
        #self.macd_state = self.macd_signals()

    def stoch_signals(self):
        K = self.tick.K
        D = self.tick.D

        if 75 < K < 90: 
            channel = 1
        elif 10 < K < 25: 
            channel = -1
        else: 
            channel = 0

        if K > D: 
            stoch = 1
        elif K < D: 
            stoch = -1

        return channel, stoch

    def bband_signals(self):
        upper = self.tick.upper
        lower = self.tick.lower
        closeMid = self.tick.closeMid
        if lower < closeMid < upper:
            channel = 0
        elif closeMid > upper:
            channel = 1
        elif closeMid < lower:
            channel = -1
        return channel

    def moving_avg_signals(self):
        sma = self.tick.sma
        ewma = self.tick.ewma
        if ewma > sma:
            sma_state = 1
        elif ewma < sma:
            sma_state = -1
        return sma_state
    