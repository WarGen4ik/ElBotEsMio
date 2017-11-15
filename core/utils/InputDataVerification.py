from core.utils.BotConn import BotConn, BotException


class InputDataVerification:
    def __init__(self, stock_exchange: str, key: str, secret: str):
        self.conn = BotConn(stock_exchange, key, secret)

    def verify_key_secret(self) -> bool:
        try:
            self.conn.get_balances()
            return True
        except BotException:
            return False

    def verify_pair(self, pair):
        try:
            self.conn.get_ticker_pair(pair)
            return True
        except KeyError:
            return False

    def verify_balance(self, depo: int, currency: str):
        balance = self.conn.get_balances()

        if depo < float(balance[currency]):
            return False
        else:
            return True
