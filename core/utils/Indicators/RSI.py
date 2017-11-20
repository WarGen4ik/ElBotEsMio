from core import utils
from core.utils.BotConn import BotConn
from core.utils.Indicators.MovingAverage import MovingAverage


class RSI:
    def __init__(self, conn: BotConn, candle_time: int, pair: str, time_stamp=utils.DAY):
        self.conn = conn
        self.candle_time = candle_time
        self.pair = pair
        self.time_stamp = time_stamp

    def calculate_rsi(self, length=14, price_list=list()):
        if not price_list:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time)

        cu_list = list()
        cd_list = list()

        n = len(price_list) - 1
        for i in range(length):
            if float(price_list[n - i]['close']) > float(price_list[n - i - 1]['close']):
                cu_list.append(float(price_list[n - i]['close']) - float(price_list[n - i - 1]['close']))
            else:
                cd_list.append(float(price_list[n - i - 1]['close']) - float(price_list[n - i]['close']))

        ma = MovingAverage(self.conn, self.candle_time, self.pair, self.time_stamp)

        rs = ma.calculate_ema(length=length, price_list=cu_list) / \
             ma.calculate_ema(length=length, price_list=cd_list)

        return 100 - (100 / (1 + rs))

    def calculate_rsi_list(self, length, price_list=list()):
        if not price_list:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time)

        ret_list = list()

        cu_list = list()
        cd_list = list()

        n = len(price_list) - 1
        while n - length > 0:
            for i in range(length):
                if float(price_list[n - i]['close']) > float(price_list[n - i - 1]['close']):
                    cu_list.append(float(price_list[n - i]['close']) - float(price_list[n - i - 1]['close']))
                else:
                    cd_list.append(float(price_list[n - i - 1]['close']) - float(price_list[n - i]['close']))

            ma = MovingAverage(self.conn, self.candle_time, self.pair, self.time_stamp)

            try:
                rs = ma.calculate_ema(length=length, price_list=cu_list) / \
                     ma.calculate_ema(length=length, price_list=cd_list)
            except ZeroDivisionError:
                rs = 100

            ret_list.append(100 - (100 / (1 + rs)))

            n -= 1

        return ret_list


# rsi = RSI(BotConn('poloniex'), utils.FIVE_MIN, 'USDT_BTC', utils.DAY)
# print(rsi.calculate_rsi_list(14))
