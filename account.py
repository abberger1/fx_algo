import requests
import pandas as pd

from config import Config

class Account:
    def __init__(self, account=1, symbol="EUR_USD"):
        tokens = pd.read_csv(Config.path_to_login)

        self.symbol = symbol
        self.venue = Config.venue
        self.streaming = Config.streaming
        self.token = tokens["token"][account]
        self.id = str(tokens["id"][account])

    def order_url(self):
        return Config.account_url+str(self.id)+'/orders/'

    def position_url(self):
        return Config.account_url+self.id+"/positions/"

    def get_headers(self):
        return {'Authorization': 'Bearer ' + str(self.token)}

    def __str__(self):
        return "DOMAIN: %s \nTOKEN: %s \nID: %s" % (self.venue, self.token, self.id)

    def __repr__(self):
        return self.__str__()
