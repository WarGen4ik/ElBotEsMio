from core.utils.BotConn import BotConn


class MovingAverage:
    def __init__(self, stock_exchange):
        self.conn = BotConn(stock_exchange)

    def calculate(self, length: int):
        price_list = self.conn.get_candle_info('USDT_BTC')
        ret_list = list()

        n = len(price_list) - 1
        while n - length > 0:
            ma_list = price_list[n - length:n]


            product = 1
            for i in ma_list:
                product *= float(i['weightedAverage'])

            ret_list.append(product / length)
            n -= 1

ma = MovingAverage('poloniex')
print(ma.calculate(5))