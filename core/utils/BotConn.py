from BotsConnections.poloniexConn import Poloniex, PoloniexError


class BotException(Exception):
    pass


class BotConn:
    Poloniex = 'poloniex'
    Bitfinex = 'bitfinex'

    def __init__(self, stock_exchange, key='', secret=''):
        self.key = key
        self.secret = secret
        self.stock_exchange = stock_exchange
        if stock_exchange == self.Poloniex:
            self.conn = Poloniex(key, secret)

    def get_ticker(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnTicker()

    def get_ticker_pair(self, pair):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnTicker()[pair]

    def get_24h_volume(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.return24hVolume()

    def get_order_book(self, pair='all', depth=20):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnOrderBook(pair, depth)

    def get_currencies(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnCurrencies()

    def get_candle_info(self, pair: str, time=300):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnChartData(pair, time)

    def get_balances(self):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnBalances()
        except (PoloniexError,) as ex:
            raise BotException(str(ex))

    def get_open_orders(self, pair='all'):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnOpenOrders(pair)

    def buy(self, pair: str, price: float, amount: float):
        if self.stock_exchange == self.Poloniex:
            return self.conn.buy(pair, price, amount)

    def sell(self, pair: str, price: float, amount: float):
        if self.stock_exchange == self.Poloniex:
            return self.conn.sell(pair, price, amount)

    def cancel_order(self, order_id: int):
        if self.stock_exchange == self.Poloniex:
            return self.conn.cancelOrder(order_id)

# currency_1 = 'BTC'
# currency_2 = 'USDT'
# bot = BotConn('poloniex', 'F4AC1AI7-JAHWF8C6-0142HBVX-J3WEKLZQ', '948c0bd67c9f673e5eb6610348d8773537e3ad36c59028a36f5aea6b344bfcd3d21645869cbc46dea4f5ce766756bd2b9bf954ba8a5cbe0ec47f0be907d941fd')
# print(bot.get_currencies())



