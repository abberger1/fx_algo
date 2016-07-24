#!/usr/bin/env python3
import trading_models
from log import ModelLog
from generic import Generic

from time import sleep
from multiprocessing import Process, Queue


class StochEventAlgo(Generic):
	def __init__(self, name):
		super().__init__(name)

		self.signal_queue = Queue()
		self.position_queue = Queue()

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


if __name__ == "__main__":
	StochEventAlgo("fx_stchevnt")
