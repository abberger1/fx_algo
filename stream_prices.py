#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import datetime as dt
import requests
import json
import sys
import pandas as pd
from multiprocessing import Process, Queue

class Tick:
        def __init__(self, time, instrument, bid, ask):
            self.time = time
            self.instrument = instrument
            self.bid = bid
            self.ask = ask

        def __str__(self):
            return "%s,%s,%s,%s" % (self.time, self.instrument, self.bid, self.ask)

class RequestPrices(Tick):
        def __init__(self, instrument, account):
            _file = pd.read_csv("/home/andrew/Downloads/Data/Keys/Tokens.txt")
            _file.index = np.array([i for i in range(1, len(_file)+1)])

            self.instrument = instrument
            self.accessToken = _file["token"][account]
            self.domain = _file["venue"][account]
            self.accountId = _file["id"][account]

        def get_prices(self):
            try:
                    s = requests.Session()
                    url = "https://stream-" + self.domain[4:] + "/v1/prices"
                    headers = {'Authorization' : 'Bearer ' + self.accessToken}
                    params = {"instruments": self.instrument, "accountId": self.accountId}
                    req = requests.Request("GET", url, headers=headers, params=params)
                    pre = req.prepare()
                    resp = s.send(pre, stream=True, verify=False)
            except Exception as e:
                    print(">>> Caught exception during request\n{}".format(e))
                    s.close()
            finally:
                    return resp

        def parse_lines(self):
            chars = "{:,}-"
            struct = {}

            for i in self.get_prices().iter_lines(1):
                i = i.decode("utf-8")
                i = i.strip("\n").split("\"")

                if "heartbeat" not in i and i!=['']:
                    instrument = i[5]
                    time = dt.datetime.strptime(i[9], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y%m%d.%H.%M.%S.%f")
                    bid = i[12][1:].strip(",")
                    ask = i[14][1:].strip("}")

                    data = Tick(time, instrument, bid, ask)
                    yield data

        def write(self, path):
                tmp = 0
                with open(path, "a") as f:
                        for tick in self.parse_lines():
                                if tick.time == tmp:
                                    continue
                                else:
                                    f.write(str(tick))
                                    f.write("\n")
                                    #print(str(tick))
                                    tmp = tick.time

def main(instruments, path):
        req = RequestPrices(instruments, 1).write(path)

if __name__ == "__main__":
        instruments = sys.argv[1]

        now = dt.datetime.now()
        year = str(now.year)
        month = str(now.month)
        day = str(now.day)

        digits = [str(x) for x in range(0, 10)]

        for digit in digits:
            if day == digit: day = "0" + day
            if month == digit: month = "0" + month

        path = "/home/andrew/Downloads/Data/Record/%s/%s/%s" % (year, month, day)
        dir = path + "/%s%s%s%s_tick" % (year, month, day, "_"+"".join("".join(instruments.split(",")).split("_")))

        if os.path.exists(path): # continue
                print(">>> Path exists\n>>> Writing in %s \n" % dir)
        else:
                print(">>> Creating %s " % path)
                subprocess.call(["mkdir", path]) # make directory

        main(instruments, dir)
