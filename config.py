class LoggingPaths:
    trades = "/home/andrew/Projects/Logs/trade_logs"
    orders = "/home/andrew/Downloads/oanda_order_logs"
    model = "/home/andrew/Downloads/model_logs"

    def __init__(self, symbol):
        self.ticks = "/home/andrew/Projects/Logs/%s_ticks" % symbol

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
