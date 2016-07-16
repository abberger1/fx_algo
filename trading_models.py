class Confs:
	page = {"fx_stchevnt": "/home/andrew/src/Oanda/.config/model.conf",
		"fx_mvgavg": "/home/andrew/src/Oanda/.config/model.conf",
		"fx_bbands": "/home/andrew/src/Oanda/.config/model.conf"}

class TradeModelError(Exception):
	messages = {0: "Model not initialized.",
	            1: "Could not open configuration file.",
	    	    2: "Configuration file contains invalid parameter.",
	    	    3: "Unknown order status. Check if trade done"}

	def __init__(self, error, message=""):
		self.error = TradeModelError.messages[error]	
		self.message = message
		self.callback()

	def callback(self):
		if self.message:
			super().__init__(self.error, self.message)
		else:
			super().__init__(self.error)

class Initial:
	def __init__(self, name):
		self.name = Confs.page[name]

	def config(self):
		try:
			field, setting = self.csv_values()
		except Exception as e:
			raise TradeModelError(0, message=e)
		return field, setting

	def csv_values(self):
		with open(self.name) as csv_file:
			try:
				p = csv_file.read().replace("\n", ",").split(",")

				field = [x for x in p if p.index(x)%2==0]
				value = [x for x in p if p.index(x)%2!=0]
			except Exception as e:
				raise TradeModelError(0, message=e)
		return field, value

class FX:
	def __init__(self, name):

		self._init = self.setup(name)

		self.COUNT = self._init[0] 
		self.LONGWIN = self._init[1]
		self.SHORTWIN = self._init[2]
		
		self.SYMBOL = self._init[3] # product code
		
		self.QUANTITY = self._init[4] # trade size
		self.MAXPOS = self._init[5] # maximum open position
		
		self.MAXLOSS = self._init[6] # per trade loss
		self.MAXGAIN = self._init[7] # per trade gain
		
		self.LIMIT = self._init[8] # for limit orders
		
	def setup(self, name):
		if name in Confs.page.keys():
			self.is_initial = Initial(name)
			try:
				values = self.is_initial.config()[1]
				return values
			except Exception as e:
				raise TradeModelError(0, message=e)
		else:
			raise TradeModelError(1, name)

	def stoch_event(self):
		self.KUP = self._init[9]
		self.KDOWN = self._init[10]
		
		self.TREND_THRESH = self._init[11] 
