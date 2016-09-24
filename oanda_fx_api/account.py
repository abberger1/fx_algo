from config import Config


class Account:
    def __init__(self, account=0):
        tokens = [x.split(',') for x in open(Config.path_to_login).read().splitlines()]
        self.id = tokens[account][0]
        self.token = tokens[account][1]
        self.venue = Config.venue
        self.streaming = Config.streaming
        self.orders = Config.account_url + self.id + '/orders/'
        self.positions = Config.account_url + self.id + "/positions/"
        self.headers = {'Authorization': 'Bearer %s' % self.token}

    def __str__(self):
        return "[=> %s (%s)" % (self.venue, self.id)

    def __repr__(self):
        return self.__str__()
