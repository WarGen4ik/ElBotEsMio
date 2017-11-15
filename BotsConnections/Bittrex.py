import urllib.request
import hmac
import hashlib
import time

#for canles
from urllib.parse import urlencode
import requests

try:
    from Crypto.Cipher import AES
except ImportError:
    encrypted = False
else:
    import getpass
    import ast
import json


BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

TICKINTERVAL_ONEMIN = 'oneMin'
TICKINTERVAL_FIVEMIN = 'fiveMin'
TICKINTERVAL_HOUR = 'hour'
TICKINTERVAL_THIRTYMIN = 'thirtyMin'
TICKINTERVAL_DAY = 'Day'

ORDERTYPE_LIMIT = 'LIMIT'
ORDERTYPE_MARKET = 'MARKET'

TIMEINEFFECT_GOOD_TIL_CANCELLED = 'GOOD_TIL_CANCELLED'
TIMEINEFFECT_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMEINEFFECT_FILL_OR_KILL = 'FILL_OR_KILL'

CONDITIONTYPE_NONE = 'NONE'
CONDITIONTYPE_GREATER_THAN = 'GREATER_THAN'
CONDITIONTYPE_LESS_THAN = 'LESS_THAN'
CONDITIONTYPE_STOP_LOSS_FIXED = 'STOP_LOSS_FIXED'
CONDITIONTYPE_STOP_LOSS_PERCENTAGE = 'STOP_LOSS_PERCENTAGE'

API_V1_1 = 'v1.1'
API_V2_0 = 'v2.0'

BASE_URL_V1_1 = 'https://bittrex.com/api/v1.1{path}?'
BASE_URL_V2_0 = 'https://bittrex.com/api/v2.0{path}?'

PROTECTION_PUB = 'pub'  # public methods
PROTECTION_PRV = 'prv'  # authenticated methods

def encrypt(key, secret, export=True, export_fn='secrets.json'):
    cipher = AES.new(getpass.getpass(
        'Input encryption password (string will not show)'))
    key_n = cipher.encrypt(key)
    secret_n = cipher.encrypt(secret)
    api = {'key': str(key_n), 'secret': str(secret_n)}
    if export:
        with open(export_fn, 'w') as outfile:
            json.dump(api, outfile)
    return api


def using_requests(request_url, apisign):
    return requests.get(
        request_url,
        headers={"apisign": apisign}
    ).json()




class BittrexError(Exception):
    """ Exception for handling bittrex api errors """
    pass


class Bittrex(object):

    def __init__(self, key, secret, calls_per_second=1, dispatch=using_requests, api_version=API_V2_0):
        self.key = str(key) if key is not None else ''
        self.secret = str(secret) if secret is not None else ''
        self.public = ['getmarkets', 'getcurrencies', 'getticker', 'getmarketsummaries', 'getmarketsummary',
                       'getorderbook', 'getmarkethistory']
        self.market = ['buylimit', 'buymarket', 'selllimit', 'sellmarket', 'cancel', 'getopenorders']
        self.account = ['getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorder', 'getorderhistory',
                        'getwithdrawalhistory', 'getdeposithistory']

        self.dispatch = dispatch
        self.call_rate = 1.0 / calls_per_second
        self.last_call = None
        self.api_version = api_version

    def decrypt(self):
        if encrypted:
            cipher = AES.new(getpass.getpass(
                'Input decryption password (string will not show)'))
            try:
                if isinstance(self.key, str):
                    self.key = ast.literal_eval(self.key)
                if isinstance(self.secret, str):
                    self.secret = ast.literal_eval(self.secret)
            except Exception:
                pass
            self.key = cipher.decrypt(self.key).decode()
            self.secret = cipher.decrypt(self.secret).decode()
        else:
            raise ImportError('"pycrypto" module has to be installed')

    def wait(self):
        if self.last_call is None:
            self.last_call = time.time()
        else:
            now = time.time()
            passed = now - self.last_call
            if passed < self.call_rate:
                # print("sleep")
                time.sleep(self.call_rate - passed)

            self.last_call = time.time()

    def _api_query(self, protection=None, path_dict=None, options=None):
        """
        Queries Bittrex
        :param request_url: fully-formed URL to request
        :type options: dict
        :return: JSON response from Bittrex
        :rtype : dict
        """

        if not options:
            options = {}

        if self.api_version not in path_dict:
            raise Exception('method call not available under API version {}'.format(self.api_version))

        request_url = BASE_URL_V2_0 if self.api_version == API_V2_0 else BASE_URL_V1_1
        request_url = request_url.format(path=path_dict[self.api_version])

        nonce = str(int(time.time() * 1000))

        if protection != PROTECTION_PUB:
            request_url = "{0}apikey={1}&nonce={2}&".format(request_url, self.key, nonce)

        request_url += urlencode(options)

        try:
           apisign = hmac.new(self.secret.encode(),
                              request_url.encode(),
                              hashlib.sha512).hexdigest()

           self.wait()

           return self.dispatch(request_url, apisign)

        except:
            return {
               'success' : False,
               'message' : 'NO_API_RESPONSE',
               'result'  : None
            }

    def query(self, method, values={}):
        if method in self.public:
            url = 'https://bittrex.com/api/v1.1/public/'
        elif method in self.market:
            url = 'https://bittrex.com/api/v1.1/market/'
        elif method in self.account:
            url = 'https://bittrex.com/api/v1.1/account/'
        else:
            return 'Something went wrong, sorry.'

        url += method + '?' + urlencode(values)

        if method not in self.public:
            url += '&apikey=' + self.key
            url += '&nonce=' + str(int(time.time()))
            signature = hmac.new(self.secret, url, hashlib.sha512).hexdigest()
            headers = {'apisign': signature}
        else:
            headers = {}

        req = urllib.request.Request(url, headers=headers)
        response = json.loads(urllib.request.urlopen(req).read())

        if response["result"]:
            return response["result"]
        else:
            return response["message"]

    def query_v2(self, method, values={}):
        url = 'https://bittrex.com/api/v2.0/pub/market/'

        url += method + '?' + urlencode(values)

        headers = {}

        req = urllib.request.Request(url, headers=headers)
        response = json.loads(urllib.request.urlopen(req).read())

        if response["result"]:
            return response["result"]
        else:
            return response["message"]

