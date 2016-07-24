class Indicators(object):
    def __init__(self, kup, kdown):
        self.KUP = kup
        self.KDOWN = kdown

    def kthresh_up_cross(self, chan, param):
        """ Upper threshold signal (self.KUP) """
        if (chan == 0) and (param > self.KUP):
            return True
        else:
            return False

    def kthresh_down_cross(self, chan, param):
        """ Lower threshold signal (self.KDOWN) """
        if (chan == 0) and (param < self.KDOWN):
            return True
        else:
            return False

    def stoch_upcross(self, K_to_D, params):
        K, D = params
        if (K_to_D  == -1) and  (K > D):
            if (K < self.KDOWN):
                return True
        else:
            return False

    def stoch_downcross(self, K_to_D, params):
        K, D = params
        if (K_to_D  == 1) and  (K < D):
            if (K > self.KUP):
                return True
        else:
            return False

class Conditions(Indicators):
    def __init__(self,kup, kdown):
        super().__init__(kup, kdown)

    def cross(self):
        if self.stoch_upcross(K_to_D, [K, D]):
            self.order_handler(tick, "buy")

        if self.stoch_downcross(K_to_D, [K, D]):
            self.order_handler(tick, "sell")

    def thresh(self):
        if self.kthresh_up_cross(channel, K):
            self.order_handler(tick, "sell")

        elif self.kthresh_down_cross(channel, K):
            self.order_handler(tick, "buy")
