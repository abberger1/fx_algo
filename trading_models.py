class TradeModelError(Exception):
	pass

class Confs:
	page = {"fx_stchevnt": "/home/andrew/src/Oanda/.config/model.conf",
		"fx_mvgavg": "/home/andrew/src/Oanda/.config/model.conf",
		"fx_bbands": "/home/andrew/src/Oanda/.config/model.conf"}

class Initial:
	def __init__(self, name):
		self.name = Confs.page[name]

	def config(self):
		try:
			name, setting = self.csv_values()
		except Exception as e:
			raise TradeModelError("Model not initialized")
		return name, setting

	def csv_values(self):
		with open(self.name) as csv_file:
			try:
				p = csv_file.read().replace("\n", ",").split(",")

				field = [x for x in p if p.index(x)%2==0]
				value = [x for x in p if p.index(x)%2!=0]
			except Exception as e:
				raise TradeModelError("Model not initialized")

		return field, value

class FX:
	def __init__(self, model):
		self.config = self.config()
	
	def setup(self, name):
		self.is_initial = Initial(name)

		if self.is_initial:
			values = self.is_initial.config()[1]
			return values
		else:
			raise TradeModelError("Model not initialized")
		return False
