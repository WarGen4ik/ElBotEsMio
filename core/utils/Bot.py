import time

import sys
from datetime import datetime

from multiprocessing import Value

from core.utils.BotConn import BotConn
from core.utils.Check_indicators_signals import Check_indicators_signals


class Bot:
    def __init__(self, conn: BotConn, currency_1: str, currency_2: str, stop_loss, profit, depo: float,
                 candle_time: int, indicators: list, v: Value, user_id: int, **kwargs):
        self.conn = conn    # Коннектор
        self.currency_1 = currency_1    # Первая валюта
        self.currency_2 = currency_2    # Вторая валюта
        self.pair = currency_1 + '_' + currency_2   # Валютная пара
        self.candle_time = candle_time  # Длительность свечи
        self.depo = depo    # Сумма для торгов
        self.check_indicators = Check_indicators_signals(indicators)
        self.user_id = user_id
        self.is_stop = v

        if profit:
            self.profit = profit / 100    # Профит (%)
        if stop_loss:
            self.stop_loss = stop_loss / 100  # Стоп-луз (%)

    def start(self):
        is_buying = False   # Покупаем ли мы валюту
        is_selling = False  # Продаем ли мы валюту
        is_sold = False   # Продана ли валюта
        is_next_step_buy = False
        is_next_step_sell = False

        stop_loss = 0.0                     # Стоп-лосс (float)
        profit = sys.float_info.max         # Профит (float)
        prev_time = 0                       # Переменная для хранения временной точки

        while self.is_stop.value:
            curr_time = int(time.time())

            # Если прошло candle_time времени
            if prev_time + self.candle_time <= curr_time:
                # Фиксируем предыдущую точку времени
                prev_time = curr_time

                # Если следующий шаг - покупка, то покупаем
                if is_next_step_buy:
                    price = self.conn.get_curr_ask_price(self.pair)
                    is_next_step_buy = False
                    print('buying')
                    is_buying = True

                # Если следующий шаг - продажа, то продаем
                if is_next_step_sell:
                    price = self.conn.get_curr_bid_price(self.pair)
                    is_next_step_sell = False
                    print('selling')
                    is_selling = True
                    is_sold = False
                    stop_loss = price - (price * self.stop_loss)
                    profit = price + (price * self.profit)

                    # TODO array of indicators
                        # is_next_step_sell = True
                        # is_under = True
                        #
                        # is_under = False
                        # # Если продано, то покупаем
                        # if is_sold:
                        #     is_next_step_buy = True

                print('sleeping')
                # print(str(avg_length_1) + '    ' + str(avg_length_2))
                print()

            # Если покупаем
            if is_buying:
                # Если нету открытых ордеров
                if not self.conn.is_any_open_order(self.pair):
                    is_buying = False
                    print('Ордер на покупку закрыт')

            # Если продаем
            if is_selling:
                # Если нету открытых ордеров
                if not self.conn.is_any_open_order(self.pair):
                    is_selling = False
                    is_sold = True
                    print('Ордер на продажу закрыт')

            # Если стоп-лосс определен
            if self.stop_loss:
                # Узнаем цену покупки и если она ниже стоп-лосса, то покупаем валюту
                price_bid = self.conn.get_curr_bid_price(self.pair)
                if price_bid <= stop_loss:
                    is_sold = False
                    print('buying')
                    print('stop loss = ' + str(stop_loss))
                    print('price_bid = ' + str(price_bid))
                    is_buying = True

                    # Назначаем стоп-лосс и профит на значения по-умолчанию
                    stop_loss = 0
                    profit = sys.float_info.max

            # Если профит определен
            if self.profit:
                # Узнаем цену продажи и если она выше чем нужный профит, то продаем
                price_ask = self.conn.get_curr_ask_price(self.pair)
                if price_ask >= profit:
                    print('selling')
                    is_selling = True
                    print('profit = ' + str(profit))
                    print('price_ask = ' + str(price_ask))

                    # Назначаем стоп-лосс и профит на значения по-умолчанию
                    stop_loss = 0
                    profit = sys.float_info.max

            # Ждем отведенное время
            time.sleep(3)
            print('sleep')


# key = 'F4AC1AI7-JAHWF8C6-0142HBVX-J3WEKLZQ'
# secret = '948c0bd67c9f673e5eb6610348d8773537e3ad36c59028a36f5aea6b344bfcd3d21645869cbc46dea4f5ce766756bd2b9bf954ba8a5cbe0ec47f0be907d941fd'
# bot = Bot(BotConn('poloniex', key, secret), 'USDT', 'BTC', 10, 50, stop_loss=2, profit=6, depo=100, am_1='sma', am_2='sma')
# bot.start()


def bot_start(kwargs):

    conn = BotConn(kwargs['stock_exchange'], kwargs['key'], kwargs['secret'])
    for indicator in kwargs['indicators']:
        indicator['pair'] = '{}_{}'.format(kwargs['currency_1'], kwargs['currency_2'])
        indicator['candle_time'] = kwargs['candle_time']
        indicator['conn'] = conn

    bot = Bot(conn=conn, **kwargs)

    bot.start()
