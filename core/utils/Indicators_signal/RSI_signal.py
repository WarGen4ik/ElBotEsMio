from core.utils.BotConn import BotConn
from core.utils.Indicators.RSI import RSI


class RSI_signal:
    def __init__(self, conn: BotConn, length, value_1, value_2, pair, candle_time):
        self.conn = conn
        self.rsi = RSI(conn, candle_time, pair)
        self.length = length
        self.value_1 = value_1
        self.value_2 = value_2

    def is_signal_to_sell(self, price_list=list()):
        rsi_value = self.rsi.calculate_rsi(self.length, price_list)
        print(rsi_value)

        if rsi_value < self.value_1:
            return False
        elif rsi_value > self.value_2:
            return True
        else:
            return None


if __name__ == '__main__':
    rsi_signal = RSI_signal(BotConn('poloniex'), 10, 30, 70, 'USDT_BTC', 300)
    print(rsi_signal.is_signal_to_sell)
