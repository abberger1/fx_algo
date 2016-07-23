import datetime as dt
from config import LoggingPaths

class Tick:
    def __init__(self, tick):

        self.symbol = tick["symbol"]
        self.path = LoggingPaths(self.symbol).ticks

        self._time = tick["timestamp"]

        self.closeBid = tick["closeBid"]
        self.closeAsk = tick["closeAsk"]
        self.spread = (self.closeAsk - self.closeBid)*10000

        self.openMid = tick["openMid"] # = avg(openAsk, openBid)
        self.highMid = tick["highMid"] # = avg(highBid, highAsk)
        self.lowMid = tick["lowMid"] # = avg(lowBid, lowAsk)
        self.closeMid = tick["closeMid"] # = avg(closeBid, closeAsk)

        self.K = 50
        self.D = 50
#        self.volume = tick["volume"]
#        self.total_volume = tick["total_volume"]
#
#
#        self.sma = tick["sma"]
#        self.ewma = tick["ewma"]
#        self.upper = tick["upper_band"]
#        self.lower = tick["lower_band"]
#        self.volatility = tick["volatility"]
#
#        self.adx = tick["adx"]
#
#        self.adf_1 = tick["ADF_1"]
#        self.adf_5 = tick["ADF_5"]
#        self.adf_10 = tick["ADF_10"]
#        self.adf_p = tick["ADF_p"]
#        self.adf_stat = tick["ADF_stat"]
#
#        self.cum_ret = tick["cum_ret"]*10000

    def __repr__(self):
        return "%s %s %s - %s" % (
	    	self._time, self.symbol,
	    	self.closeBid, self.closeAsk)

    def write_tick(self):
        with open(self.path, "a") as file:
            file.write(self.__repr__())
