#!/home/andrew/anaconda3/bin/python3.5
from multiprocessing import Process, Queue
class Initialize:
	def __init__(self, path_to_config):
		self.path_to_config = path_to_config

	def init_model(self):
		try:
			name, setting = self.set_params()
		except Exception as e:
			print("Failed to initialize:\n%s" % e)	
			return False
		return name, setting

	def set_params(self):
		params = open(self.path_to_config)
		params = params.read().replace("\n", ",").split(",")

		name = [x for x in params if params.index(x)%2==0]
		setting = [x for x in params if params.index(x)%2!=0]

		return name, setting
			
class Model:
	def __init__(self, path_to_config):

		self.is_initialized = Initialize(path_to_config).init_model()
		param = self.get_parameters()
	
		self.COUNT = param[0]
		self.LONGWIN = param[1]
		self.SHORTWIN = param[2]
		
		self.SYMBOL = param[3]
		
		self.QUANTITY = param[4]
		self.MAXPOS = param[5]
		
		self.MAXLOSS = param[6]
		self.MAXGAIN = param[7] 
		
		self.LIMIT = param[8]
		
		self.KUP = param[9]
		self.KDOWN = param[10]
		
		self.TREND_THRESH = param[11] 
		
		self.signal_queue = Queue()
		self.position_queue = Queue()
		
		#self.model_log().start()

	def __repr__(self):
		return "SYMBOL:%s\nCOUNT:%s\nMAXPOS:%s\n" % (
			self.SYMBOL, self.COUNT, self.MAXPOS)

	def get_parameters(self):
		if self.is_initialized:
	    		return self.is_initialized[1]
		else:
	    		print("Warning: model not initialized")
		return False

if __name__ == "__main__":
	model = Model("/home/andrew/src/Oanda/.config/model.conf")
	if model.is_initialized:
		print(model)
	else:
		print("Failed to initialize")
