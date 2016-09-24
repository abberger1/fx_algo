import datetime as dt
import pandas as pd
import requests
import json


class StreamPrices(object):
    def __init__(self, account, instrument):
        self.account = account
        self.instrument = instrument

    def stream(self):
        try:
            s = requests.Session()
            headers = self.account.headers
            params = {"instruments": self.instrument,
                      "accessToken": self.account.token,
                      "accountId": self.account.id}
            req = requests.Request("GET", self.account.streaming, headers=headers, params=params)
            pre = req.prepare()
            resp = s.send(pre, stream=True, verify=False)
        except Exception as e:
            print(">>> Caught exception during request\n{}".format(e))
            s.close()
        finally:
            return resp

    def prices(self):
        for tick in self.stream():
            try:
                tick = json.loads(str(tick, "utf-8"))
            except json.decoder.JSONDecodeError as e:
                prev_tick = '%s' % (str(tick, "utf-8"))
                print(prev_tick)
                continue
            if "tick" in tick.keys():
                tick = tick["tick"]
                print(tick)


class GetCandles(object):
    def __init__(self, account, count, symbol, granularity):
        self.account = account
        self.count = count
        self.symbol = symbol
        self.granularity = granularity
        self.headers = self.account.headers
        self.params = {'instrument' : self.symbol,
                       'granularity' : self.granularity,
                       'count' : int(self.count)}

    def request(self):
        try:
            req = requests.get(self.account.venue+"/v1/candles", headers=self.headers, params=self.params).json()
            candles = pd.DataFrame(req['candles'])
            candles["symbol"] = self.symbol
            candles.index = candles["time"].map(lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"))
            candles["timestamp"] = candles.index.map(lambda x: x.timestamp())
            for x in ['open', 'high', 'low', 'close']:
                candles['%sMid' % x] = (candles['%sAsk' % x] + candles['%sBid' % x]) / 2
            return candles
        except Exception as e:
            print('%s\n>>> Error: No candles in JSON response:' % e)
            return False
