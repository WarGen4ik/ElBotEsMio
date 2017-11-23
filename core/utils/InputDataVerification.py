from core.utils.BotConn import BotConn, BotException


class VerifyException(Exception):
    pass


class InputDataVerification:
    def __init__(self, stock_exchange: str, key='', secret=''):
        self.conn = BotConn(stock_exchange, key, secret)

    def verify_key_secret(self) -> bool:
        try:
            self.conn.get_balances()
            return True
        except BotException:
            raise VerifyException('Key or/and secret are not valid')

    def verify_pair(self, pair):
        try:
            self.conn.get_ticker_pair(pair)
            return True
        except KeyError:
            raise VerifyException('INVALID_MARKET')
        except BotException as ex:
            raise VerifyException(str(ex))

    def verify_balance(self, depo: float, currency: str):
        if depo < self.conn.get_balance(currency):
            return False
        else:
            raise VerifyException('Not enough balance')

    def verify_and_get_balance_percent(self, depo_percent: float, currency: str):
        depo = self.conn.get_balance(currency)
        return depo * depo_percent

    def verify_all(self, **kwargs):
        if 'depo_percent' in kwargs:
            verify_depo = True
        else:
            verify_depo = self.verify_balance(kwargs['depo'], kwargs['currency'])
        return self.verify_pair(kwargs['pair']) and verify_depo
