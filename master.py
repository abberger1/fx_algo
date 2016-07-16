#!/home/andrew/anaconda3/bin/python3.5
import trading_models
from log import ModelLog
from compute import Signals, Compute
from positions import Positions, ExitPosition, PnL
from order import OrderHandler

from multiprocessing import Process, Queue
from time import sleep

class StochEventAlgo(trading_models.FX):
	def __init__(self, name):
		super().__init__(name)
		self.stoch_event()
	
		self.signal_queue = Queue()
		self.position_queue = Queue()
		
		#self.model_log().start()

	def __repr__(self):
		return "SYMBOL:%s\nCOUNT:%s\nMAXPOS:%s\n" % (
			self.SYMBOL, self.COUNT, self.MAXPOS)

	def model_log(self):
	    return ModelLog(self.SYMBOL,
	                    self.COUNT,
	                    self.LONGWIN,
	                    self.SHORTWIN)
	
	def signals(self):
	    return Signals(self.COUNT,
	                   self.SYMBOL,
	                   self.LONGWIN,
	                   self.SHORTWIN,
	                   "S5")
	
	def positions(self):
	    return Positions().checkPosition(self.SYMBOL)
	
	def kthresh_up_cross(self, chan, param):
	    """ Upper threshold signal (self.KUP) """
	    if (chan == 0) and (param > self.KUP):
	        return True
	    else:
	        return False
	
	def kthresh_down_cross(self, chan, param):
	    """ Lower threshold signal (self.KDOWN) """
	    if (chan == 0) and (param < self.KDOWN):
	        return True
	    else:
	        return False
	
	def stoch_upcross(self, K_to_D, params):
	    K, D = params
	    if (K_to_D  == -1) and  (K > D):
	        if (K < self.KDOWN):
	            return True
	    else:
	        return False
	
	def stoch_downcross(self, K_to_D, params):
	    K, D = params
	    if (K_to_D  == 1) and  (K < D):
	        if (K > self.KUP):
	            return True
	    else:
	        return False
	
	def close_out(self, tick, position, profit_loss):
	    close = ExitPosition().closePosition(position, profit_loss, tick)
	    self.model_log().exit(close._time, close.price, close.id, profit_loss)
	
	def risk_control(self):
	    while True:
	        tick = self.signal_queue.get()[2]
	        
	        position = self.positions()
	        self.position_queue.put(position.units)
	
	        if position.units != 0:
	            lower_limit = self.MAXLOSS*(position.units/10000)
	            upper_limit = self.MAXGAIN*(position.units/10000)
	
	            profit_loss = PnL(tick, position).get_pnl()
	
	            # close position max loss
	            if profit_loss < lower_limit:
	                self.close_out(tick, position, profit_loss)
	
	            # close position max gain
	            if profit_loss > upper_limit:
	                self.close_out(tick, position, profit_loss)
	
	def order_handler(self, tick, side):
	    trade = OrderHandler(self.SYMBOL, tick, side, self.QUANTITY).send_order()
	
	    if trade.reject:
	            self.model_log().reject(trade._time, trade.code, trade.message, tick)
	    else:
	            self.model_log().order(trade.time, trade.price, trade.id, "market", side)
	
	def signal_listen(self):
	    while True:
	        channel, K_to_D, tick = self.signal_queue.get()
	        K, D = tick.K, tick.D
	
	        print(tick)
	        position = self.position_queue.get()
	
	        if self.stoch_upcross(K_to_D, [K, D]):
	            self.order_handler(tick, "buy")
	
	        if self.stoch_downcross(K_to_D, [K, D]):
	            self.order_handler(tick, "sell")
	
		#writer = tick.write_tick()
	
	        if self.kthresh_up_cross(channel, K):
	            self.order_handler(tick, "sell")
	
	        elif self.kthresh_down_cross(channel, K):
	            self.order_handler(tick, "buy")

	        if self.kthresh_up_cross(channel, K):
	            self.order_handler(tick, "buy")
	
	        elif self.kthresh_down_cross(channel, K):
	            self.order_handler(tick, "sell")
	
	def trade_model(self):
	    model = self.signals()
	
	    tick = model.tick
	    channel = model.channel
	    K_to_D = model.stoch
	
	    while True:
	        self.signal_queue.put([channel, K_to_D, tick])
	
	        sleep(5)
	
	        channel = model.channel
	        K_to_D = model.stoch
	
	        model = self.signals()
	        tick = model.tick
	
	def main(self):
	    model = Process(target=self.trade_model)
	    risk = Process(target=self.risk_control)
	    signal = Process(target=self.signal_listen)
	
	    model.start(); risk.start(); signal.start()
	    model.join(); risk.join(); signal.join()


if __name__ == "__main__":
	StochEventAlgo("fx_stchevnt").main()
