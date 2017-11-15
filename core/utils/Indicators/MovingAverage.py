from core import utils
from core.utils.BotConn import BotConn


class MovingAverage:
    def __init__(self, conn: BotConn, candle_time: int, pair: str, time_stamp=utils.DAY):
        self.conn = conn
        self.candle_time = candle_time
        self.time_stamp = time_stamp
        self.pair = pair

    def calculate_sma_list(self, length: int, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)
        ret_list = list()

        n = len(price_list) - 1
        while n - length > 0:
            ma_list = price_list[n - length:n]

            product = 0
            if isinstance(ma_list[0], dict):
                for i in ma_list:
                    product += float(i['close'])
            else:
                for i in ma_list:
                    product += i

            ret_list.append(product / length)
            n -= 1

        return ret_list

    def calculate_sma(self, length: int, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)

        n = len(price_list)
        ma_list = price_list[n - length:n]

        product = 0
        if isinstance(ma_list[0], dict):
            for i in ma_list:
                product += float(i['close'])
        else:
            for i in ma_list:
                product += i

        return product / length

    def calculate_ema(self, length: int, p=0.01, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)

        n = len(price_list)
        p = 2 / (length + 1)
        ma_list = price_list[n - length:n]

        return self._ema(ma_list, p)

    def calculate_ema_list(self, length: int, p=0.01, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)
        ret_list = list()

        n = len(price_list)
        p = 2 / (length + 1)

        while n - length > 0:
            ma_list = price_list[n - length:n]
            ret_list.append(self._ema(ma_list, p))

            n -= 1

        return ret_list

    def _ema(self, ma_list: list, p: float, count_steps=0, avg=0.0):
        if len(ma_list) != 1:
            if isinstance(ma_list[0], dict):
                return (float(ma_list[-1]['close']) * p) + \
                       (self._ema(ma_list[:-1], p, count_steps + 1, avg + float(ma_list[-1]['close'])) * (1 - p))
            else:
                return (float(ma_list[-1]) * p) + \
                       (self._ema(ma_list[:-1], p, count_steps + 1, avg + float(ma_list[-1])) * (1 - p))
        else:
            if isinstance(ma_list[0], dict):
                return float(ma_list[0]['close'])
            else:
                return float(ma_list[0])

    def calculate_smma(self, length: int, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)

        n = len(price_list) - 1
        ma_list = price_list[n - length:n]

        return self._smma(ma_list)

    def _smma(self, ma_list):
        if ma_list:
            return (float(self._smma(ma_list[:-1])) * (len(ma_list) - 1) + float(ma_list[-1]['close'])) / len(ma_list)
        else:
            return 0

    def calculate_lwma(self, length: int, price_list=list()):
        if price_list:
            pass
        else:
            price_list = self.conn.get_candle_info(self.pair, self.candle_time, self.time_stamp)

        n = len(price_list) - 1
        ma_list = price_list[n - length:n]

        sum1 = 0
        sum2 = 0
        count = 1
        for x in ma_list:
            sum1 += float(x['close']) * count
            sum2 += count
            count += 1

        return sum1/sum2


if __name__ == '__main__':
    am = MovingAverage(BotConn('poloniex'), 300, 'USDT_BTC')
    print(am.calculate_lwma(14))
    # a = [1,2,3,4]
    # a.reverse()
    # print(a)
