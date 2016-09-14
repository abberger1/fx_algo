#!/usr/bin/env python3
import datetime as dt
import requests
import json
import sys

from account import Account


class StreamPrices(Account):
        def __init__(self, instrument):
            super().__init__()
            self.instrument = instrument

        @profile
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

        @profile
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

def main(instruments):
        req = StreamPrices(instruments).prices()


if __name__ == "__main__":
        instruments = sys.argv[1]
        main(instruments)
