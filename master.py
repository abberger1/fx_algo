#!/usr/bin/env python3
import trading_models
from log import ModelLog
from order import OrderHandler
from compute import Signals, Compute
from positions import Positions, ExitPosition, PnL

from time import sleep
from multiprocessing import Process, Queue




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
