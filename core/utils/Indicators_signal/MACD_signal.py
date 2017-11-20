from pprint import pprint

from core import utils
from core.utils.BotConn import BotConn
from core.utils.Indicators.MACD import MACD


class MACD_signal:
    def __init__(self, conn: BotConn, candle_time: int, pair: str, length_1=26, length_2=12, length_3=9):
        self.conn = conn
        self.candle_time = candle_time
        self.macd = MACD(conn=conn, candle_time=candle_time, pair=pair, length_1=length_1, length_2=length_2,
                         length_3=length_3, time_stamp=utils.DAY * 12)

    @property
    def is_signal_to_sell(self, price_list=list()):
        macd_values = self.macd.calculate_list(price_list)

        pprint(macd_values)
        print('{}   {}'.format(macd_values['signal'][-1], macd_values['macd'][-1]))
        if macd_values['signal'][-1] > macd_values['macd'][-1]:
            return True
        else:
            return False


if __name__ == '__main__':
    macd_signal = MACD_signal(BotConn('poloniex'), 300, 'USDT_BTC')
    print(macd_signal.is_signal_to_sell)