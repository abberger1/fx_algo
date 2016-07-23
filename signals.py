from compute import Compute


class Signals(Compute):
    def __init__(self, count, symbol, longWin, shortWin, granularity="S5"):
        super().__init__(count, symbol, longWin, shortWin, granularity)

        self.channel, self.stoch = 50, 50
        self.bbands_channel = 0

        #self.mavg_state = self.moving_avg_signals()
        #self.macd_state = self.macd_signals()

    def stoch_signals(self):
        K = self.tick.K
        D = self.tick.D

        if self.KUP < K < 90:
            channel = 1
        elif 10 < K < self.KDOWN:
            channel = -1
        else:
            channel = 0

        if K > D:
            stoch = 1
        elif K < D:
            stoch = -1

        return channel, stoch

    def bband_signals(self):
        upper = self.tick.upper
        lower = self.tick.lower
        closeMid = self.tick.closeMid
        if lower < closeMid < upper:
            channel = 0
        elif closeMid > upper:
            channel = 1
        elif closeMid < lower:
            channel = -1
        return channel

    def moving_avg_signals(self):
        sma = self.tick.sma
        ewma = self.tick.ewma
        if ewma > sma:
            sma_state = 1
        elif ewma < sma:
            sma_state = -1
        return sma_state
