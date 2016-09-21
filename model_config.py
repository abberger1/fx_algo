
class LoggingPaths:
    trades = "/home/andrew/Projects/Logs/trade_logs"
    orders = "/home/andrew/Downloads/oanda_order_logs"
    model = "/home/andrew/Downloads/model_logs"

    def __init__(self, symbol):
        self.ticks = "/home/andrew/Projects/Logs/%s_ticks" % symbol


class ModelLog:
    def __init__(self, SYMBOL, COUNT, LONGWIN, SHORTWIN):
        self.path = LoggingPaths.model
        self.SYMBOL = SYMBOL
        self.COUNT = COUNT
        self.LONGWIN = LONGWIN
        self.SHORTWIN = SHORTWIN

    def start(self):
        start = "%s,%s,%s,%s,%s" % (
            dt.datetime.now().timestamp(), self.SYMBOL,
            self.COUNT, self.LONGWIN, self.SHORTWIN)
        self._write_to_log(start)
        return True

    def order(self, TIME, PRICE, ID, TYPE, SIDE):
        order = "%s,%s,%s,%s,%s" % (TIME, self.SYMBOL, SIDE, PRICE, ID)
        self._write_to_log(order)
        return True

    def reject(self, TIME, CODE, MSG, tick):
        reject = "%s,%s,reject,%s,%s" % (
                  TIME, self.SYMBOL, CODE, MSG)
        mktSnap = "%s,%s,%s,%s,%s,%s" % (
                  tick._time, tick.closeBid,
                  tick.closeAsk, tick.volatility,
                  tick.trend, tick.spread)
        self._write_to_log(reject)
        self._write_rejects(mktSnap)
        return True

    def exit(self, TIME, PRICE, ID, PNL):
        exit = "%s,%s,%s,%s,%s" % (
            TIME, self.SYMBOL, PRICE, PNL, ID)
        self._write_to_log(exit)
        return True

    def _write_to_log(self, msg):
        with open(self.path, "a") as file:
                file.write(msg+"\n")

    def _write_rejects(self, msg):
        with open(self.path+"_rejects", "a") as file:
                file.write(msg+"\n")


class Config:
    path_to_login = "/home/andrew/src/python/oanda/Tokens"
    venue = "https://api-fxpractice.oanda.com"
    streaming = "https://stream-fxpractice.oanda.com/v1/prices"
    account_url = venue + "/v1/accounts/"


class Confs:
	page = {"fx_stchevnt": "/home/andrew/src/python/oanda/fx_stoch_event_algo/model.conf",
    		"fx_mvgavg": "/home/andrew/src/python/oanda/fx_stoch_event_algo/model.conf",
    		"fx_bbands": "/home/andrew/src/python/oanda/fx_stoch_event_algo/model.conf"}


class TradeModelError(Exception):
	messages = {0: "Model not initialized.",
	            1: "Could not open configuration file.",
	    	    2: "Configuration file contains invalid parameter.",
	    	    3: "Unknown order status. Check if trade done."}

	def __init__(self, error, message=""):
		self.error = TradeModelError.messages[error]
		self.message = message
		self.callback()

	def callback(self):
		if self.message:
			super().__init__(self.error, self.message)
		else:
			super().__init__(self.error)


class FX(object):
        def __init__(self, name):
                self._init = self.setup(name) # calls Initial
                self.COUNT = self._init[0]
                self.LONGWIN = self._init[1]
                self.SHORTWIN = self._init[2]
                self.SYMBOL = self._init[3]
                self.QUANTITY = self._init[4]
                self.MAXPOS = self._init[5]
                self.MAXLOSS = self._init[6]
                self.MAXGAIN = self._init[7]
                self.LIMIT = self._init[8]
                self.MODEL = []

        def setup(self, name):
                if name in Confs.page.keys():
                        try:
                                return Initial(name).config()[1] # second column
                        except Exception as e:
                                raise TradeModelError(0, message=e)
                else:
                        raise TradeModelError(1, name)

        def stoch_event(self):
                self.MODEL.append("stoch")
                self.KUP = self._init[9]
                self.KDOWN = self._init[10]

        def bband_event(self):
                self.MODEL.append("bband")

        def mavg_event(self):
                self.MODEL.append("mavg")

        def macd_event(self):
                self.MODEL.append("macd")

        def adx_event(self):
                self.MODEL.append("adx")

