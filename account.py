import requests
import pandas as pd

import logging
logging.basicConfig(filename="/home/andrew/Projects/Logs/account.py.log")

class Config:
    path_to_params = "/home/andrew/.config/Oanda/trade_model.txt"
    path_to_login = "/home/andrew/Downloads/Data/Keys/Tokens"
    
    venue = "https://api-fxpractice.oanda.com"
    account_url = venue + "/v1/accounts/"

class Account:
    def __init__(self, account=1, symbol="EUR_USD"):
        tokens = pd.read_csv(Config.path_to_login)

        self.symbol = symbol
        self.venue = Config.venue
        self.token = tokens["token"][account]
        self.id = str(tokens["id"][account])

    def get_url(self):
        return Config.account_url+str(self.id)+'/orders/'
    
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