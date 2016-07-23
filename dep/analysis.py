#!/usr/bin/env python3
import datetime as dt
import pandas as pd

from account import Account
from compute import Compute

class Analysis:
    def __init__(self, year, month, day, **kwargs):
        self.year = year
        self.month = month
        self.day = day

        start = dt.datetime(year, month, day)
        end = dt.datetime(year, month, day+1)

        logs = "/home/andrew/Downloads/model_logs"
        trades = "/home/andrew/Downloads/trade_logs"
        ticks = "/home/andrew/Downloads/ticks"

        logs = pd.read_csv(logs,
                        names=["time", "symbol", "side/price", "price/pnl", "id"])
        logs.index = logs["time"].map(lambda x: dt.datetime.utcfromtimestamp(x))

        trades = pd.read_csv(trades,
                        names=["time", "id", "side", "symbol", "units",
                                "price", "trend", "volatility", "K",
                                "ask", "bid", "volume"])
        trades.index = trades["time"].map(lambda x: dt.datetime.utcfromtimestamp(x))

        ticks = pd.read_csv(ticks,
                        usecols=[0, 1, 2, 3],
                        names=["time", "bid", "ask", "volume"],
                        dtype={"bid":float, "ask":float, "volume":int})
        ticks.index = ticks["time"].map(lambda x: dt.datetime.utcfromtimestamp(x))

        self.ticks = ticks.ix[(ticks.index>start)&(ticks.index<end)].sort_values("time")
        self.trades = trades.ix[(trades.index>start)&(trades.index<end)].sort_values("time")
        self.logs = logs.ix[(logs.index>start)&(logs.index<end)].sort_values("time")

        del self.ticks["time"]

    def history(self):
        acc = Account().get_history()
        acc.index = acc["time"].map(lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"))
        self.acc =  acc = acc.ix[acc.index>dt.datetime(self.year, self.month, self.day)]

        starting_balance = acc.ix[0]["accountBalance"]
        ending_balance = acc.ix[-1]["accountBalance"]
        self.returns = acc["pl"].sum()
        total_trades = self.acc.ix[(self.acc["side"]=="buy")|(self.acc["side"]=="sell")]

        buys = acc.ix[acc["side"] == "buy"]
        sells = acc.ix[acc["side"] == "sell"]

        wins = acc.ix[acc["pl"] > 0]
        losses = acc.ix[acc["pl"] < 0]

        print("<%s> - <%s>\n\t\tBeginning Balance: %s\n\t\tEnding Balance: %s\n\n\t\tTrades: %s\n\t\tWin: %s Lose: %s\n\t\tLongs: %s Shorts: %s\n\n\t\tPnL: %s" % (self.ticks.index[0], self.ticks.index[-1], starting_balance, ending_balance, total_trades["pl"].count(), wins["pl"].count(), losses["pl"].count(), buys["pl"].count(), sells["pl"].count(), self.returns))

    def daily(self):
        longs = self.trades.ix[self.trades["side"] == "buy"]
        shorts = self.trades.ix[self.trades["side"] == "sell"]

        long_ex = self.trades.ix[self.trades["side" ] == "long"]
        short_ex = self.trades.ix[self.trades["side" ] == "short"]

        win_long =  long_ex.ix[long_ex["symbol"] > 0]
        win_short =  short_ex.ix[short_ex["symbol"] > 0]

        lose_long =  long_ex.ix[long_ex["symbol"] < 0]
        lose_short =  short_ex.ix[short_ex["symbol"] < 0]

        rejects = self.logs.ix[self.logs["side/price"]=="reject"]
        orders = self.logs.ix[(self.logs["side/price"]=="buy")|(self.logs["side/price"]=="sell")]

if __name__ =="__main__":
    now = dt.datetime.now()
    year, month, day = now.year, now.month, now.day
    Analysis(year, month, day).history()