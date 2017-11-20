from core import utils
from core.utils.BotConn import BotConn
from core.utils.Indicators.MovingAverage import MovingAverage


class MACD:
    def __init__(self, conn: BotConn, candle_time: int, pair: str, time_stamp=utils.DAY, length_1=26, length_2=12,
                 length_3=9):
        self.conn = conn
        self.candle_time = candle_time
        self.length_1 = length_1
        self.length_2 = length_2
        self.length_3 = length_3
        self.pair = pair
        self.time_stamp = time_stamp

    def calculate_list(self, p=0.01, price_list=list()):
        ret_list = dict()

        ma = MovingAverage(self.conn, self.candle_time, self.pair, self.time_stamp)

        ema_list_1 = ma.calculate_ema_list(self.length_1, p, price_list)
        ema_list_2 = ma.calculate_ema_list(self.length_2, p, price_list)

        ret_list['macd'] = list()
        for i in range(len(ema_list_1)):
            ret_list['macd'].append(ema_list_2[i] - ema_list_1[i])

        ret_list['macd'].reverse()
        ret_list['signal'] = [ma.calculate_sma(self.length_3, ret_list['macd']),]
        return ret_list
