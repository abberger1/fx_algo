import statsmodels.tsa.stattools as ts
import talib

from prices import StreamPrices, GetCandles
from config import LoggingPaths, FX
from position import Positions
from account import Account


class Tick:
    def __init__(self, tick):
        self.symbol = tick["symbol"]
        self.path = LoggingPaths(self.symbol).ticks
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
        self.channel, self.stoch = 50, 50
        self.bbands_channel = 0
        #self.mavg_state = self.moving_avg_signals()
        #self.macd_state = self.macd_signals()

    def stoch_signals(self):
        K, D = self.tick.K, self.tick.D
        if self.KUP < K < 90:
            channel = 1
        elif 10 < K < self.KDOWN:
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
        StreamPrices(account, symbol).prices()



#class Initialize:
#	def __init__(self, path_to_config):
#		self.path_to_config = path_to_config
#
#	def init_model(self):
#		try:
#			name, setting = self.set_params()
#		except Exception as e:
#			print("Failed to initialize:\n%s" % e)	
#			return False
#		return name, setting
#
#	def set_params(self):
#		params = open(self.path_to_config)
#		params = params.read().replace("\n", ",").split(",")
#		name = [x for x in params if params.index(x)%2==0]
#		setting = [x for x in params if params.index(x)%2!=0]
#		return name, setting

#class Parameters:
#	def __init__(self, path_to_config):
#		self.is_initialized = Initialize(path_to_config).init_model()
#		param = self.get_parameters()
#		self.COUNT = param[0]
#		self.LONGWIN = param[1]
#		self.SHORTWIN = param[2]
#		self.SYMBOL = param[3]
#		self.QUANTITY = param[4]
#		self.MAXPOS = param[5]
#		self.MAXLOSS = param[6]
#		self.MAXGAIN = param[7] 
#		self.LIMIT = param[8]
#		self.KUP = param[9]
#		self.KDOWN = param[10]
#		self.TREND_THRESH = param[11] 
#		self.signal_queue = Queue()
#		self.position_queue = Queue()
#		#self.model_log().start()
#
#	def __repr__(self):
#		return "SYMBOL:%s\nCOUNT:%s\nMAXPOS:%s\n" % (
#			self.SYMBOL, self.COUNT, self.MAXPOS)
#
#	def get_parameters(self):
#		if self.is_initialized:
#	    		return self.is_initialized[1]
#		else:
#	    		print("Warning: model not initialized")
#		return False
#
#
#
#class Indicators(object):
#    def __init__(self, kup, kdown):
#        self.KUP = kup
#        self.KDOWN = kdown
#
#    def kthresh_up_cross(self, chan, param):
#        """ Upper threshold signal (self.KUP) """
#        if (chan == 0) and (param > self.KUP):
#            return True
#        else:
#            return False
#
#    def kthresh_down_cross(self, chan, param):
#        """ Lower threshold signal (self.KDOWN) """
#        if (chan == 0) and (param < self.KDOWN):
#            return True
#        else:
#            return False
#
#    def stoch_upcross(self, K_to_D, params):
#        K, D = params
#        if (K_to_D  == -1) and  (K > D):
#            if (K < self.KDOWN):
#                return True
#        else:
#            return False
#
#    def stoch_downcross(self, K_to_D, params):
#        K, D = params
#        if (K_to_D  == 1) and  (K < D):
#            if (K > self.KUP):
#                return True
#        else:
#            return False
#
#class Conditions(Indicators):
#    def __init__(self,kup, kdown):
#        Indicators.__init__(kup, kdown)
#
#    def cross(self):
#        if self.stoch_upcross(K_to_D, [K, D]):
#            self.order_handler(tick, "buy")
#
#        if self.stoch_downcross(K_to_D, [K, D]):
#            self.order_handler(tick, "sell")
#
#    def thresh(self):
#        if self.kthresh_up_cross(channel, K):
#            self.order_handler(tick, "sell")
#
#        elif self.kthresh_down_cross(channel, K):
#            self.order_handler(tick, "buy")
#
#
#class Generic(FX):
#        def __init__(self, name):
#            FX.__init__(name)
#            self.stoch_event()
#
#        def signals(self):
#            return Signals(self.COUNT,
#                           self.SYMBOL,
#                           self.LONGWIN,
#                           self.SHORTWIN,
#                           "S5")
#
#        def order_handler(self, tick, side):
#            trade = OrderHandler(self.SYMBOL,
#                            tick,
#                            side,
#                            self.QUANTITY).send_order()
#            if trade.reject:
#                print("[!]  -- Order rejected -- ")
#            return trade
#
#        def positions(self):
#            position = Positions(self.SYMBOL).checkPosition()
#            return position
#
#        def close_out(self, tick, position, profit_loss):
#            close = ExitPosition().closePosition(position,
#                                                profit_loss,
#                                                tick)
#            return close
#
#        def check_position(self, tick):
#           # while True:
#           #     tick = self.signal_queue.get()[2]
#
#            # get positions
#            position = self.positions()
#            #self.position_queue.put(position.units)
#
#            if position.units != 0:
#                self.risk_control(tick, position)
#
#        def risk_control(self, tick, position):
#                lower_limit = self.MAXLOSS*(position.units/self.QUANTITY)
#                upper_limit = self.MAXGAIN*(position.units/self.QUANTITY)
#                profit_loss = PnL(tick, position).get_pnl()
#
#                if profit_loss < lower_limit:
#                    self.close_out(tick,
#                                    position,
#                                    profit_loss)
#
#                if profit_loss > upper_limit:
#                    self.close_out(tick,
#                                    position,
#                                    profit_loss)


#class StochEventAlgo(Generic):
#	def __init__(self, name):
#		Generic.__init__(name)
#		self.signal_queue = Queue()
#		self.position_queue = Queue()
#
#	def signal_listen(self):
#	    while True:
#	        channel, K_to_D, tick = self.signal_queue.get()
#	        K, D = tick.K, tick.D
#	        print(tick)
#	        position = self.position_queue.get()
#
#	def trade_model(self):
#	    model = self.signals()
#	    tick = model.tick
#	    channel = model.channel
#	    K_to_D = model.stoch
#
#	    while True:
#	        self.signal_queue.put([channel, K_to_D, tick])
#	        sleep(5)
#	        channel = model.channel
#	        K_to_D = model.stoch
#	        model = self.signals()
#	        tick = model.tick
