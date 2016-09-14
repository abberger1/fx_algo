#!/usr/bin/env python3
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc
from matplotlib.transforms import Bbox

import talib
from signals import Signals
from positions import Positions, PnL

plt.rcParams["axes.grid"] = True
plt.rcParams["axes.formatter.useoffset"] = False

class Candles(Signals):
    def __init__(self, count, symbol, granularity="S5"):
        longWin = count * 0.75
        shortWin = longWin * 0.5
        super().__init__(count, symbol, longWin, shortWin)
        
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_position(Bbox([[0.125, 0.22], [0.9, 0.79]]))
        self.ax2 = self.ax.twinx()
        self.ax2.set_position(Bbox([[0.125, 0.22], [0.9, 0.79]]))
        self.ax3 = self.ax.twinx()
        self.ax3.set_position(Bbox([[0.125, 0.79], [0.9, 0.9]]))
        self.ax3.set_ylim([0, 100])
        self.ax4 = self.ax.twinx()
        self.ax4.set_ylim([0, 100])
        self.ax4.set_position(Bbox([[0.125, 0.1], [0.9, 0.22]]))
        
        self.model = Signals(count, 
                             symbol,
                             longWin, 
                             shortWin,
                             granularity=granularity)
        
        cand_gran = "1T"
        
        self.candles = self.model.candles[["sma", "ewma", "K", "D", "upper_band", "lower_band", "closeMid", "volume"]].resample(cand_gran).ohlc()
        self.candles["time"] = self.candles.index.map(lambda x: dt.datetime.timestamp(x))
        self.candles.index = self.candles["time"]

        self._candles = list(zip(self.candles["time"], 
                              self.candles["closeMid"]["open"], 
                              self.candles["closeMid"]["high"], 
                              self.candles["closeMid"]["low"], 
                              self.candles["closeMid"]["close"],
                              self.candles["volume"]["close"]))
        
        self.doji = pd.Series(talib.CDLDOJI(self.candles["closeMid"]["open"].values, 
                                  self.candles["closeMid"]["high"].values, 
                                  self.candles["closeMid"]["low"].values, 
                                  self.candles["closeMid"]["close"].values), index=self.candles.index)
        self.doji_index = self.doji.ix[self.doji == 100].index
        self.doji_sigs = self.candles.ix[self.doji_index]
        
        self.hammers = pd.Series(talib.CDLHAMMER(self.candles["closeMid"]["open"].values, 
                                  self.candles["closeMid"]["high"].values, 
                                  self.candles["closeMid"]["low"].values, 
                                  self.candles["closeMid"]["close"].values), index=self.candles.index)
        self.hammer_sigs_index = self.hammers.ix[self.hammers == 100].index
        self.hammer_buys = self.candles.ix[self.hammer_sigs_index]
        
        self.invhammers = pd.Series(talib.CDLINVERTEDHAMMER(self.candles["closeMid"]["open"].values, 
                                  self.candles["closeMid"]["high"].values, 
                                  self.candles["closeMid"]["low"].values, 
                                  self.candles["closeMid"]["close"].values), index=self.candles.index)
        self.invhammer_sigs_index = self.invhammers.ix[self.invhammers == 100].index
        self.invhammer_sell = self.candles.ix[self.invhammer_sigs_index]
        
        self.tasuki = pd.Series(talib.CDLTASUKIGAP(self.candles["closeMid"]["open"].values, 
                                  self.candles["closeMid"]["high"].values, 
                                  self.candles["closeMid"]["low"].values, 
                                  self.candles["closeMid"]["close"].values), index=self.candles.index)
        self.tasuki_index = self.tasuki.ix[self.tasuki == 100].index
        self.tasuki_sigs = self.candles.ix[self.tasuki_index]
        
        self.linearreg = pd.Series(talib.LINEARREG(self.candles["closeMid"]["close"].values, 64), index=self.candles.index)
        self.TSF = pd.Series(talib.TSF(self.candles["closeMid"]["close"].values), index=self.candles.index)
        self.RSI = pd.Series(talib.RSI(self.candles["closeMid"]["close"].values), index=self.candles.index)
        
        candlestick_ohlc(self.ax,
                         self._candles, 
                         colorup="g", 
                         colordown="r",
                         width=75,
                         alpha=50)
        
        #self.ax.plot(self.hammer_sigs_index, self.hammer_buys["closeMid"]["close"], "^", label="hammer", markersize=11)
        #self.ax.plot(self.invhammer_sigs_index, self.invhammer_sell["closeMid"]["close"], "v", label="invhammer", markersize=11)
        
        #self.ax.plot(self.doji_index, self.doji_sigs["closeMid"]["close"], ".", label="doji", markersize=11)
        #self.ax.plot(self.tasuki_index, self.tasuki_sigs["closeMid"]["close"], ".", label="tasuki", markersize=11)
                                   
        #self.ax.legend(loc="best")
        
        #self.ax.plot(self.candles["time"], self.linearreg, linewidth=0.75)
        #self.ax.plot(self.candles["time"], self.candles["ewma"]["close"], linewidth=0.75, label="wma")
                                   
        self.ax.plot(self.candles["time"], self.candles["upper_band"]["close"], linewidth=0.75, label="upper")
        self.ax.plot(self.candles["time"], self.candles["lower_band"]["close"], linewidth=0.75, label="lower")
        
        for label in self.ax.xaxis.get_ticklabels():
            label.set_visible(False)
        
        self.ax2.set_ylim([0, self.candles["volume"]["close"].max()*4])
        self.ax2.fill_between(self.candles["time"], self.candles["volume"]["close"], label="volume", alpha=0.35)
        #self.ax2.legend(loc="best")
        
        self.ax3.plot(self.candles["time"], self.candles["D"]["close"], label="D")
        self.ax3.plot(self.candles["time"], self.candles["K"]["close"], label="K")
        self.ax3.legend(loc="best")
        
        self.ax3.set_title("%s %s %s - %s" % (count, symbol, granularity, cand_gran), loc="left")
        
        self.ax4.plot(self.candles["time"], self.RSI, label="RSI")
        
        self.position = Positions().checkPosition("EUR_USD")
        if self.position.units != 0:
            pnl = PnL(self.model.tick, self.position).get_pnl()
            print(str(self.model.tick)+"\nPOSITION: %s %s @ %s PnL: %s"%(self.position.side, self.position.units, self.position.price, pnl))
        else:
            print(self.model.tick)

        plt.show()


if __name__ == '__main__':
    from sys import argv
    Candles(int(argv[1]), argv[2])
