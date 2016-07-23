#!/usr/bin/env python3
import trading_models
from log import ModelLog

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
