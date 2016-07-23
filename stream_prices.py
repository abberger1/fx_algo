#!/usr/bin/env python3
import datetime as dt
import requests
import json
import sys

from account import Account

DEBUG = 0


class StreamPrices(Account):
        def __init__(self, instrument):
            super().__init__()
            self.instrument = instrument

        def stream(self):
            try:
                    s = requests.Session()
                    headers = self.get_headers()
                    params = {"instruments": self.instrument,
                            "accessToken": self.token,
                            "accountId": self.id}

                    req = requests.Request("GET",
                                            self.streaming,
                                            headers=headers,
                                            params=params)
                    pre = req.prepare()
                    resp = s.send(pre, stream=True, verify=False)
            except Exception as e:
                    print(">>> Caught exception during request\n{}".format(e))
                    s.close()
            finally:
                    return resp

        def prices(self):
            for tick in self.stream():
                tick = json.loads(str(tick, "utf-8"))
#                if "heartbeat" in tick.keys():
#                    heartbeat = tick["heartbeat"]
#                    print(heartbeat)
                if "tick" in tick.keys():
                    tick = tick["tick"]
                    print(tick)

def main(instruments):
        req = StreamPrices(instruments).prices()

if __name__ == "__main__":
        instruments = sys.argv[1]
        main(instruments)
