import trading_models
from compute import Compute
from signals import Signals
from order import OrderHandler
from positions import (
            Positions,
            ExitPosition,
            PnL)


class Generic(trading_models.FX):
        def __init__(self, name):
            super().__init__(name)
            self.stoch_event()

        def signals(self):
            return Signals(self.COUNT,
                           self.SYMBOL,
                           self.LONGWIN,
                           self.SHORTWIN,
                           "S5")

        def order_handler(self, tick, side):
            trade = OrderHandler(self.SYMBOL,
                            tick,
                            side,
                            self.QUANTITY).send_order()
            if trade.reject:
                print("[!] Order rejected")

        def positions(self):
            position = Positions().checkPosition(self.SYMBOL)
            return position

        def close_out(self, tick, position, profit_loss):
            close = ExitPosition().closePosition(position,
                                                profit_loss,
                                                tick)
            return close

        def check_position(self, tick):
           # while True:
           #     tick = self.signal_queue.get()[2]

            # get positions
            position = self.positions()
            #self.position_queue.put(position.units)

            if position.units != 0:
                self.risk_control(tick, position)

        def risk_control(self, tick, position):
                lower_limit = self.MAXLOSS*(position.units/self.QUANTITY)
                upper_limit = self.MAXGAIN*(position.units/self.QUANTITY)
                profit_loss = PnL(tick, position).get_pnl()

                if profit_loss < lower_limit:
                    self.close_out(tick,
                                    position,
                                    profit_loss)

                if profit_loss > upper_limit:
                    self.close_out(tick,
                                    position,
                                    profit_loss)

if __name__ == "__main__":
        Generic("fx_stchevnt")
