from core.utils.BotConn import BotConn
from core.utils.Indicators_signal.MACD_signal import MACD_signal
from core.utils.Indicators_signal.MA_signal import MA_signal
from core.utils.Indicators_signal.RSI_signal import RSI_signal


class Check_indicators_signals:
    def __init__(self, ma=None, ma_args=None, rsi=None, rsi_args=None, macd=None, macd_args=None):
        self.methods = list()
        if ma:
            self.methods.append(MA_signal(**ma_args))
        if rsi:
            self.methods.append(RSI_signal(**rsi_args))
        if macd:
            self.methods.append(MACD_signal(**macd_args))

    @property
    def check_sell(self):
        for method in self.methods:
            if method.is_signal_to_sell is not True:
                return False
        return True

    @property
    def check_buy(self):
        for method in self.methods:
            if method.is_signal_to_sell is not False:
                return False
        return True


if __name__ == '__main__':
    conn = BotConn('poloniex')
    price_list = conn.get_candle_info('USDT_BTC')
    cis = Check_indicators_signals(ma='sma', ma_args={'conn': BotConn('poloniex'), 'length_1': 10, 'length_2': 50,
                                                      'ma_1': 'sma', 'ma_2': 'sma', 'pair': 'USDT_BTC', 'candle_time': 300,
                                                      'price_list': price_list})
    print(cis.check_sell)
