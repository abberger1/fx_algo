from order import OrderHandler
from compute import Signals, Compute
from positions import Positions, ExitPosition, PnL

class Generic:
	def signals(self):
	    return Signals(self.COUNT,
	                   self.SYMBOL,
	                   self.LONGWIN,
	                   self.SHORTWIN,
	                   "S5")

	def model_log(self):
	    return ModelLog(self.SYMBOL,
	                    self.COUNT,
	                    self.LONGWIN,
	                    self.SHORTWIN)


	def order_handler(self, tick, side):
	    trade = OrderHandler(self.SYMBOL,
                            tick,
                            side,
                            self.QUANTITY).send_order()

	    if trade.reject:
	            self.model_log().reject(trade._time, trade.code,
                                    trade.message, tick)
	    else:
	            self.model_log().order(trade.time, trade.price,
                                trade.id, "market", side)

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
