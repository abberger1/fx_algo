from matplotlib.dates import date2num
import datetime as dt
import pandas as pd
import requests
import json
from account import Account


class GetCandles(Account):
    def __init__(self, count, symbol, granularity):
        super().__init__()
        self.count = count
        self.symbol = symbol
        self.granularity = granularity
        self.headers = self.get_headers()
        self.params = {'instrument'  : self.symbol,
                       'granularity' : self.granularity,
                       'count'       : int(self.count)}

    def request(self):
        try:
            req = requests.get(self.venue+"/v1/candles", 
                               headers=self.headers,
                               params=self.params).json()

            candles = pd.DataFrame(req['candles'])
            candles["symbol"] = self.symbol
            candles.index = candles["time"].map(lambda x: dt.datetime.strptime(x,"%Y-%m-%dT%H:%M:%S.%fZ"))
            candles["timestamp"] = candles.index.map(lambda x: x.timestamp())

            for x in ['close', 'low', 'high', 'open']:
                candles["%sMid" % x] = (candles["%sAsk" % x]+candles["%sBid" % x]) / 2
            return candles
        except Exception as e:
            print('%s\n>>> Error: No candles in JSON response:'%e)
            return False


if __name__ == '__main__':
    from sys import argv
    candles = GetCandles(int(argv[1]), argv[2], argv[3]).request()
    print(candles.tail())
