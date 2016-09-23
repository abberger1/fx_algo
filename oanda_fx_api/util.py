import statsmodels.tsa.stattools as ts
import datetime as dt
import pandas as pd
import numpy as np
import requests
import talib
import json

from config import (
                    LoggingPaths,
                    FX
                    )
from account import Account


class Initialize(Account):
    def __init__(self):
        Account.__init__(self)


class StreamPrices:
    def __init__(self, account, instrument):
        self.account = account
        self.instrument = instrument

    def stream(self):
        try:
            s = requests.Session()
            headers = self.account.get_headers()
            params = {"instruments": self.instrument,
                      "accessToken": self.account.token,
                      "accountId": self.account.id}
            req = requests.Request("GET",
                                    self.account.streaming,
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
            try:
                tick = json.loads(str(tick, "utf-8"))
            except json.decoder.JSONDecodeError as e:
                prev_tick = '%s' % (str(tick, "utf-8"))
                print(prev_tick)
                continue
            if "tick" in tick.keys():
                tick = tick["tick"]
                print(tick)


class GetCandles:
    def __init__(self, account, count, symbol, granularity):
        self.account = account
        self.count = count
        self.symbol = symbol
        self.granularity = granularity
        self.headers = account.get_headers()
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
            candles["closeMid"] = (candles["closeAsk"]+candles["closeBid"]) / 2
            candles["lowMid"] = (candles["lowAsk"]+candles["lowBid"]) / 2
            candles["highMid"] = (candles["highAsk"]+candles["highBid"]) / 2
            candles["openMid"] = (candles["openAsk"]+candles["openBid"]) / 2
            return candles
        except Exception as e:
            print('%s\n>>> Error: No candles in JSON response:'%e)
            return False


class Tick:
    def __init__(self, tick):
        self.symbol = tick["symbol"]
        self.path = LoggingPaths(self.symbol).ticks
        self._time = tick["timestamp"]
        self.closeBid = tick["closeBid"]
        self.closeAsk = tick["closeAsk"]
        self.spread = (self.closeAsk - self.closeBid) * 10000
        self.openMid = tick["openMid"]
        self.highMid = tick["highMid"]
        self.lowMid = tick["lowMid"]
        self.closeMid = tick["closeMid"]
        self.K = tick['K']
        self.D = tick['D']
        self.volume = tick["volume"]
        self.total_volume = tick["total_volume"]
        self.sma = tick["sma"]
        self.ewma = tick["ewma"]
        self.upper = tick["upper_band"]
        self.lower = tick["lower_band"]
        self.volatility = tick["volatility"]
        self.adx = tick["adx"]
        self.adf_1 = tick["ADF_1"]
        self.adf_5 = tick["ADF_5"]
        self.adf_10 = tick["ADF_10"]
        self.adf_p = tick["ADF_p"]
        self.adf_stat = tick["ADF_stat"]
        self.cum_ret = tick["cum_ret"]*10000

    def __repr__(self):
        return "%s %s %s - %s" % (
	    	self._time, self.symbol,
	    	self.closeBid, self.closeAsk)

    def write_tick(self):
        with open(self.path, "a") as file:
            file.write(self.__repr__())


class Compute(GetCandles):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity):
        GetCandles.__init__(self, account, count, symbol, granularity)
        self.candles = self.request()
        self._open = self.candles["openMid"].values
        self.high = self.candles["highMid"].values
        self.low = self.candles["lowMid"].values
        self.close = self.candles["closeMid"].values
        self.longWin = longWin
        self.shortWin = shortWin
        self.candles["total_volume"] = self.candles["volume"].sum()
        self.stoch_osc()
        self.adf_test()
        self.cum_ret()
        self.moving_average()
        self.bbands()
        self.adx()
        self.tick = Tick(self.candles.ix[self.candles.index[-1]])

    def adf_test(self):
        test = ts.adfuller(self.candles["closeMid"], maxlag=1)
        adf_crit = test[4]
        self.candles["ADF_1"] = adf_crit["1%"]
        self.candles["ADF_5"] = adf_crit["5%"]
        self.candles["ADF_10"] = adf_crit["10%"]
        self.candles["ADF_p"] = test[1]
        self.candles["ADF_stat"] = test[0]

    def stoch_osc(self):
        self.candles["K"], self.candles["D"] = talib.STOCH(self.high, 
                                                           self.low, 
                                                           self.close,
                                                           slowk_period=52,
                                                           fastk_period=68,
                                                           slowd_period=52)

    def moving_average(self):
        self.candles["sma"] = talib.SMA(self.close, timeperiod=self.shortWin)
        self.candles["ewma"] = talib.EMA(self.close, timeperiod=self.shortWin)

    def macd(self):
        self.candles["macd"], self.candles["macd_sig"], self.candles["macd_hist"] = talib.MACD(self.close)

    def bbands(self):
        self.candles["upper_band"], self.candles["mid"], self.candles["lower_band"] = talib.BBANDS(self.close, timeperiod=self.longWin)
        self.candles["volatility"] = (self.candles["upper_band"] - self.candles["lower_band"])*10000

    def cum_ret(self):
        self.candles["cum_ret"] = self.candles["closeMid"].pct_change().cumsum()

    def adx(self):
        self.candles["adx"] = talib.ADX(self.high, self.low, self.close, timeperiod=48)


class Signals(Compute):
    def __init__(self, account, count, symbol, longWin, shortWin, granularity="S5"):
        Compute.__init__(self, account, count, symbol, longWin, shortWin, granularity)
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


class MostRecentReject:
    def __init__(self, account, order, params):
        self.account = account
        self._time = dt.datetime.now().timestamp()
        self.code = order["code"]
        self.message = order["message"]
        self.params = params
        self.reject = True # will not log

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # code == 23
        return "[=> REJECT %s %s @ %s (%s)" % (self._time, 
                                               self.params['side'], 
                                               self.params['price'], 
                                               self.message)


class MostRecentTrade:
    """
    Market Orders --> response from Oanda POST
    Receives and handles the order data
    """
    def __init__(self, order, tick):
        self.order = order
        self.tick = tick
        self.path = LoggingPaths.trades
        self.closed = self.closed_trade()
        self.opened = self.opened_trade()
        self.reject = False

    def closed_trade(self):
        if ("tradesClosed" in self.order) and self.order["tradesClosed"]:
            self.time = dt.datetime.strptime(self.order["time"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            try:
                self.side = self.order["tradesClosed"][0]["side"]
                self.id = self.order["tradesClosed"][0]["id"]
                self.units = self.order["tradesClosed"][0]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                return True
            except KeyError as e:
                print("Caught exception in closed_trade\n%s"%e)
        else:
            pass

    def opened_trade(self):
        if ("tradeOpened" in self.order) and self.order["tradeOpened"]:
            self.time = dt.datetime.strptime(self.order["time"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            try:
                self.side = self.order["tradeOpened"]["side"]
                self.id = self.order["tradeOpened"]["id"]
                self.units = self.order["tradeOpened"]["units"]
                self.instrument = self.order["instrument"]
                self.price = self.order["price"]
                return True
            except KeyError as e:
                print(self.order)
                print("Caught exception in opened_trade\n%s"%e)
        else:
            pass

    def __repr__(self):
        return str(self.order)


class OrderHandler:
    def __init__(self, account, symbol, tick, side, quantity, kind="market", price=0):
        self.account = account
        self.url = account.order_url()
        self.headers = account.get_headers()
        self.side = side
        self.quantity = quantity
        self.tick = tick
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.kind = kind
        self.price = price
        self.expiry = str(int((dt.datetime.utcnow().timestamp())))

    def execute_price(self):
        if self.side == "buy":
            _price = self.tick.closeBid - 0.0001
        elif self.side == "sell":
            _price = self.tick.closeAsk + 0.0001
        else:
            raise NotImplementedError(
                   ">>> Invalid side !! \n>>> Order not complete.")
        return _price

    def market_order(self):
        _price = self.execute_price()
        params = {'instrument': self.symbol,
                  'side': self.side,
                  'type': self.kind,
                  'units': self.quantity,
                  "price": _price,
                  "upperBound": _price+0.00005,
                  "lowerBound": _price-0.00005}
        return params

    def limit_order(self):
        self.headers["X-Accept-Datetime-Format"] = "UNIX"
        params = {'instrument': self.symbol,
                  'side': self.side,
                  'type': self.kind,
                  'units': self.quantity,
                  "price": self.price,
                  "expiry": self.expiry}
        return params

    def _send_order(self):
        if self.kind == "limit":
            params = self.limit_order()
        elif self.kind == "market":
            params = self.market_order()
        else:
            raise NotImplementedError(
            ">>> Invalid order type %s, exiting. TRADE NOT DONE" % self.kind)
        try:
            resp = requests.post(self.url, headers=self.headers, data=params, verify=False).json()
            return resp, params
        except Exception as e:
            print(">>> Caught exception sending order\n%s"%(e))
            return False

    def send_order(self):
        order, price = self._send_order()
        if order:
            # market order
            if "tradeOpened" in order.keys():
                order = MostRecentTrade(order, self.tick)
            # limit order
            elif "orderOpened" in order.keys():
                order = MostRecentOrder(order, self.tick)
            # reject
            elif "code" in order.keys():
                if order["code"] == 23 or order["code"] == 22:
                    order = MostRecentReject(order, price)
                    print(order)
                else:
                    raise NotImplementedError(
                    "order[\'code\'] not an integer or != 23 or 22")
            return order
        else:
            print(ValueError(
            "%s>>> Order not complete\n"%order))
            return False


class PnL:
    def __init__(self, tick, position):
        self.tick = tick
        self.position = position

    def get_pnl(self):
        if self.position.side == "short":
            pnl = (self.position.price - self.tick.closeAsk) * self.position.units
        elif self.position.side == "long":
            pnl = (self.tick.closeBid - self.position.price) * self.position.units
        return pnl


class MostRecentPosition:
    def __init__(self, side, price, units):
        self.side = side
        self.price = price
        self.units = units
        self.order = [self.side, self.units, self.price]

    def __repr__(self):
        return "SIDE: %s PRICE: %s UNITS: %s\n" % (
                self.side, np.mean(self.price), self.units)


class Positions(Initialize):
    def __init__(self, account, symbol):
        self.account = account
        self.headers = account.get_headers()
        self.symbol = symbol

    def _checkPosition(self):
        try:
            url = self.account.position_url() + self.symbol
            params = {'instruments': self.symbol,
                       "accountId": self.account.id}
            req = requests.get(url, headers=self.headers, data=params).json()
        except Exception as e:
            print(">>> Error returning position\n%s\n%s"%(str(e), req))
            return False

        if "code" in req:
            #print(req)
            return False
        elif 'side' in req:
            _side = req['side']
            units = req['units']
            price = req['avgPrice']
            if _side == 'sell': 
                side = 'short'
            elif _side == 'buy': 
                side = 'long'
            position = {'side': side,
                        'units': units,
                        'price': price}
            return position
        else:
            print(req)
            return False

    def checkPosition(self):
        position = self._checkPosition()
        if position:
            position = MostRecentPosition(position["side"],
                                          position["price"],
                                          position["units"])
            return position
        else:
            return MostRecentPosition(0, 0, 0)


class MostRecentExit:
    def __init__(self, position, side, profit_loss, tick):
        self._time = tick._time
        self.id = ("|").join([str(x) for x in position["ids"]])
        self.instrument = position["instrument"]
        self.price = position["price"]
        self.units = position["units"]
        self.profit_loss = profit_loss
        self.side = side
        self.tick = tick
        self.path = LoggingPaths.trades


class ExitPosition:
    def __init__(self, account):
        self.account = account
        self.url = self.position_url() + self.symbol
        self.headers = account.get_headers()

    def _closePosition(self, symbol):
        try:
            req = requests.delete(self.url,
                                  headers=self.headers).json()
        except Exception as e:
            print('Unable to delete positions: \n', str(e))
            return req
        try:
            ids = req['ids']
            instrument = req['instrument']
            units = req['totalUnits']
            price = req['price']
            orderData = {'ids': ids, 'instrument': instrument,
                            'units': units, 'price': price}
            return orderData
        except Exception as e:
            print('Caught exception closing positions: \n%s\n%s'%(str(e), req))
            return False

    def closePosition(self, position, profit_loss, tick):
        exit = self._closePosition("EUR_USD")
        if exit["units"] != 0:
            exit = MostRecentExit(exit,
                                  position.side,
                                  profit_loss, tick)
            exit.write_exit()
            return exit
        else:
            print(">>> No positions removed\n(%s)"%position)
            return False






if __name__ == '__main__':
    from sys import argv

    if len(argv) > 1:
        symbol = argv[1]
        account = Account()
        tick = Signals(account, 1250, symbol, 900, 450).tick
        #order = OrderHandler(argv[3], tick, symbol, argv[2]).send_order()
        position = Positions(account, symbol).checkPosition()

        print(position)
        print(tick)
        StreamPrices(account, symbol).prices()



#class Initialize:
#	def __init__(self, path_to_config):
#		self.path_to_config = path_to_config
#
#	def init_model(self):
#		try:
#			name, setting = self.set_params()
#		except Exception as e:
#			print("Failed to initialize:\n%s" % e)	
#			return False
#		return name, setting
#
#	def set_params(self):
#		params = open(self.path_to_config)
#		params = params.read().replace("\n", ",").split(",")
#		name = [x for x in params if params.index(x)%2==0]
#		setting = [x for x in params if params.index(x)%2!=0]
#		return name, setting
#
#			
#class Parameters:
#	def __init__(self, path_to_config):
#		self.is_initialized = Initialize(path_to_config).init_model()
#		param = self.get_parameters()
#		self.COUNT = param[0]
#		self.LONGWIN = param[1]
#		self.SHORTWIN = param[2]
#		self.SYMBOL = param[3]
#		self.QUANTITY = param[4]
#		self.MAXPOS = param[5]
#		self.MAXLOSS = param[6]
#		self.MAXGAIN = param[7] 
#		self.LIMIT = param[8]
#		self.KUP = param[9]
#		self.KDOWN = param[10]
#		self.TREND_THRESH = param[11] 
#		self.signal_queue = Queue()
#		self.position_queue = Queue()
#		#self.model_log().start()
#
#	def __repr__(self):
#		return "SYMBOL:%s\nCOUNT:%s\nMAXPOS:%s\n" % (
#			self.SYMBOL, self.COUNT, self.MAXPOS)
#
#	def get_parameters(self):
#		if self.is_initialized:
#	    		return self.is_initialized[1]
#		else:
#	    		print("Warning: model not initialized")
#		return False
#
#
#
#class Indicators(object):
#    def __init__(self, kup, kdown):
#        self.KUP = kup
#        self.KDOWN = kdown
#
#    def kthresh_up_cross(self, chan, param):
#        """ Upper threshold signal (self.KUP) """
#        if (chan == 0) and (param > self.KUP):
#            return True
#        else:
#            return False
#
#    def kthresh_down_cross(self, chan, param):
#        """ Lower threshold signal (self.KDOWN) """
#        if (chan == 0) and (param < self.KDOWN):
#            return True
#        else:
#            return False
#
#    def stoch_upcross(self, K_to_D, params):
#        K, D = params
#        if (K_to_D  == -1) and  (K > D):
#            if (K < self.KDOWN):
#                return True
#        else:
#            return False
#
#    def stoch_downcross(self, K_to_D, params):
#        K, D = params
#        if (K_to_D  == 1) and  (K < D):
#            if (K > self.KUP):
#                return True
#        else:
#            return False
#
#class Conditions(Indicators):
#    def __init__(self,kup, kdown):
#        Indicators.__init__(kup, kdown)
#
#    def cross(self):
#        if self.stoch_upcross(K_to_D, [K, D]):
#            self.order_handler(tick, "buy")
#
#        if self.stoch_downcross(K_to_D, [K, D]):
#            self.order_handler(tick, "sell")
#
#    def thresh(self):
#        if self.kthresh_up_cross(channel, K):
#            self.order_handler(tick, "sell")
#
#        elif self.kthresh_down_cross(channel, K):
#            self.order_handler(tick, "buy")
#
#
#class Generic(FX):
#        def __init__(self, name):
#            FX.__init__(name)
#            self.stoch_event()
#
#        def signals(self):
#            return Signals(self.COUNT,
#                           self.SYMBOL,
#                           self.LONGWIN,
#                           self.SHORTWIN,
#                           "S5")
#
#        def order_handler(self, tick, side):
#            trade = OrderHandler(self.SYMBOL,
#                            tick,
#                            side,
#                            self.QUANTITY).send_order()
#            if trade.reject:
#                print("[!]  -- Order rejected -- ")
#            return trade
#
#        def positions(self):
#            position = Positions(self.SYMBOL).checkPosition()
#            return position
#
#        def close_out(self, tick, position, profit_loss):
#            close = ExitPosition().closePosition(position,
#                                                profit_loss,
#                                                tick)
#            return close
#
#        def check_position(self, tick):
#           # while True:
#           #     tick = self.signal_queue.get()[2]
#
#            # get positions
#            position = self.positions()
#            #self.position_queue.put(position.units)
#
#            if position.units != 0:
#                self.risk_control(tick, position)
#
#        def risk_control(self, tick, position):
#                lower_limit = self.MAXLOSS*(position.units/self.QUANTITY)
#                upper_limit = self.MAXGAIN*(position.units/self.QUANTITY)
#                profit_loss = PnL(tick, position).get_pnl()
#
#                if profit_loss < lower_limit:
#                    self.close_out(tick,
#                                    position,
#                                    profit_loss)
#
#                if profit_loss > upper_limit:
#                    self.close_out(tick,
#                                    position,
#                                    profit_loss)
#
#
#class StochEventAlgo(Generic):
#	def __init__(self, name):
#		Generic.__init__(name)
#		self.signal_queue = Queue()
#		self.position_queue = Queue()
#
#	def signal_listen(self):
#	    while True:
#	        channel, K_to_D, tick = self.signal_queue.get()
#	        K, D = tick.K, tick.D
#	        print(tick)
#	        position = self.position_queue.get()
#
#	def trade_model(self):
#	    model = self.signals()
#	    tick = model.tick
#	    channel = model.channel
#	    K_to_D = model.stoch
#
#	    while True:
#	        self.signal_queue.put([channel, K_to_D, tick])
#	        sleep(5)
#	        channel = model.channel
#	        K_to_D = model.stoch
#	        model = self.signals()
#	        tick = model.tick
#
#class MostRecentOrder:
#    """
#    Limit Orders --> response from Oanda POST
#    """
#    def __init__(self, account, order, tick):
#        self.account = account
#        self._time = dt.datetime.now().timestamp()
#        self.price = order["price"]
#        self.instrument = order["instrument"]
#        self.side = order["orderOpened"]["side"]
#        self.id = order["orderOpened"]["id"]
#        self.units = order["orderOpened"]["units"]
#        self.expiry = order["orderOpened"]["expiry"]
#        self.tick = tick
#        self.path = LoggingPaths.orders
#        self.reject = False
#
#    def working(self):
#        try:
#                resp = requests.get(self.url, headers=self.headers, verify=False).json()
#                return resp
#        except Exception as e:
#                raise ValueError(">>> Caught exception retrieving orders: %s"%e)
#
#    def delete(self):
#        try:
#                resp = requests.request("DELETE", self.url,
#                                        headers=self.headers, verify=False).json()
#                return resp
#        except Exception as e:
#                raise ValueError(">>> Caught exception retrieving orders: %s"%e)
