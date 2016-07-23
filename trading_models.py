from config import Confs, TradeModelError


class Initial:
	def __init__(self, name):
		self.name = Confs.page[name]

	def config(self):
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

		self.COUNT = self._init[0] # lookback period
		self.LONGWIN = self._init[1]
		self.SHORTWIN = self._init[2]
		self.SYMBOL = self._init[3] # product code
		self.QUANTITY = self._init[4] # trade size
		self.MAXPOS = self._init[5] # maximum open position
		self.MAXLOSS = self._init[6] # per trade loss
		self.MAXGAIN = self._init[7] # per trade gain
		self.LIMIT = self._init[8] # for limit orders

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
		self.KUP = self._init[9]
		self.KDOWN = self._init[10]
        self.MODEL.append("stoch")

    def bband_event(self):
        self.MODEL.append("bband")

    def mavg_event(self):
        self.MODEL.append("mavg")

    def macd_event(self):
        self.MODEL.append("macd")

    def adx_event(self):
        self.MODEL.append("adx")
