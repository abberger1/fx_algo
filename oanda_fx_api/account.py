from config import Config


class Account:
    def __init__(self, account=0):
        tokens = [x.split(',') for x in open(Config.path_to_login).read().splitlines()]
        print('reading tokens')
        self.token = tokens[account][1]
        self.id = tokens[account][0]
        self.venue = Config.venue
        self.streaming = Config.streaming

    def order_url(self):
        return Config.account_url + self.id + '/orders/'

    def position_url(self):
        return Config.account_url + self.id + "/positions/"

    def get_headers(self):
        return {'Authorization': 'Bearer %s' % self.token}

    def __str__(self):
        return "[=> %s (%s)" % (self.venue, self.id)

    def __repr__(self):
        return self.__str__()
