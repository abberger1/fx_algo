import datetime as dt
from config import LoggingPaths

class ModelLog:
    def __init__(self, SYMBOL, COUNT, LONGWIN, SHORTWIN):
        self.path = LoggingPaths.model

        self.SYMBOL = SYMBOL
        self.COUNT = COUNT
        self.LONGWIN = LONGWIN
        self.SHORTWIN = SHORTWIN

    def start(self):
        start = "%s,%s,%s,%s,%s" % (
            dt.datetime.now().timestamp(), self.SYMBOL,
            self.COUNT, self.LONGWIN, self.SHORTWIN)
        self._write_to_log(start)
        return True

    def order(self, TIME, PRICE, ID, TYPE, SIDE):
        order = "%s,%s,%s,%s,%s" % (TIME, self.SYMBOL, SIDE, PRICE, ID)
        self._write_to_log(order)
        return True

    def reject(self, TIME, CODE, MSG, tick):
        reject = "%s,%s,reject,%s,%s" % (
                  TIME, self.SYMBOL, CODE, MSG)
        mktSnap = "%s,%s,%s,%s,%s,%s" % (
                  tick._time, tick.closeBid,
                  tick.closeAsk, tick.volatility,
                  tick.trend, tick.spread)
        self._write_to_log(reject)
        self._write_rejects(mktSnap)
        return True

    def exit(self, TIME, PRICE, ID, PNL):
        exit = "%s,%s,%s,%s,%s" % (
            TIME, self.SYMBOL, PRICE, PNL, ID)
        self._write_to_log(exit)
        return True

    def _write_to_log(self, msg):
        with open(self.path, "a") as file:
                file.write(msg+"\n")

    def _write_rejects(self, msg):
        with open(self.path+"_rejects", "a") as file:
                file.write(msg+"\n")
