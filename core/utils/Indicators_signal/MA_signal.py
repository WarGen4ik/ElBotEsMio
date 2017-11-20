from core.utils.BotConn import BotConn
from core.utils.Indicators.MovingAverage import MovingAverage


class MA_signal:
    def __init__(self, conn: BotConn, length_1, length_2, ma_1, ma_2, pair, candle_time, **kwargs):
        self.is_under = None
        self.conn = conn
        self.method = self._get_method(ma_1, ma_2, pair, candle_time)
        self.kwargs_1 = kwargs.copy()
        self.kwargs_2 = kwargs.copy()
        self.kwargs_1['length'] = length_1
        self.kwargs_2['length'] = length_2

    def is_signal_to_sell(self, price_list=list()):
        avg_1 = self.method(price_list=price_list, **self.kwargs_1)
        avg_2 = self.method(price_list=price_list, **self.kwargs_2)

        if avg_1 > avg_2:
            self.is_under = False
        else:
            self.is_under = True

        return self.is_under

    def _get_method(self, ma_1, ma_2, pair, candle_time):
        mov_avg = MovingAverage(self.conn, candle_time, pair)
        if ma_1 == 'sma':
            return mov_avg.calculate_sma
        elif ma_1 == 'ema':
            return mov_avg.calculate_ema
        elif ma_1 == 'smma':
            return mov_avg.calculate_smma
        elif ma_1 == 'lwma':
            return mov_avg.calculate_lwma

        if ma_2 == 'sma':
            return mov_avg.calculate_sma
        elif ma_2 == 'ema':
            return mov_avg.calculate_ema
        elif ma_2 == 'smma':
            return mov_avg.calculate_smma
        elif ma_2 == 'lwma':
            return mov_avg.calculate_lwma


if __name__ == '__main__':
    ma_signal = MA_signal(BotConn('poloniex'), 10, 50, 'sma', 'sma', 'USDT_BTC', 300)
    print(ma_signal.is_signal_to_sell)

