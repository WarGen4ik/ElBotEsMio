import time

import sys
from datetime import datetime

from core.utils.BotConn import BotConn
from core.utils.Indicators.MovingAverage import MovingAverage


class Bot:
    def __init__(self, conn: BotConn, currency_1: str, currency_2: str, length_1: int, length_2: int,
                 stop_loss: float, profit: float, depo: float, am_1: str, am_2: str, candle_time=300):
        self.conn = conn    # Коннектор
        self.currency_1 = currency_1    # Первая валюта
        self.currency_2 = currency_2    # Вторая валюта
        self.pair = currency_1 + '_' + currency_2   # Валютная пара
        self.length_1 = length_1    # Длинна первой плавающей средней
        self.length_2 = length_2    # Длинна второй плавающей средней
        self.candle_time = candle_time  # Длительность свечи
        self.depo = depo    # Сумма для торгов
        self.am_1 = am_1    # Первый метод плавающей средней
        self.am_2 = am_2    # Второй метод плавающей средней

        if profit:
            self.profit = profit / 100    # Профит (%)
        if stop_loss:
            self.stop_loss = stop_loss / 100  # Стоп-луз (%)

    def start(self, **kwargs):
        is_buying = False   # Покупаем ли мы валюту
        is_selling = False  # Продаем ли мы валюту
        is_sold = False   # Продана ли валюта
        is_next_step_buy = False
        is_next_step_sell = False

        stop_loss = 0.0                     # Стоп-лосс (float)
        profit = sys.float_info.max         # Профит (float)
        prev_time = 0                       # Переменная для хранения временной точки

        while True:
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


# key = 'F4AC1AI7-JAHWF8C6-0142HBVX-J3WEKLZQ'
# secret = '948c0bd67c9f673e5eb6610348d8773537e3ad36c59028a36f5aea6b344bfcd3d21645869cbc46dea4f5ce766756bd2b9bf954ba8a5cbe0ec47f0be907d941fd'
# bot = Bot(BotConn('poloniex', key, secret), 'USDT', 'BTC', 10, 50, stop_loss=2, profit=6, depo=100, am_1='sma', am_2='sma')
# bot.start()


# def bot_start(v, user, stock_exchange, pair, msg, **kwargs):
#     import bot.settings
#     import django
#     import os
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.path.join(bot.settings.BASE_DIR, 'bot', 'settings'))
#     django.setup()
#     from core.models import Logs
#     # while v.value:
#     #     print('hello' + str(name))
#     #     time.sleep(3)
#     Logs.objects.create(user=user, stock_exchange=stock_exchange, pair=pair, date=datetime.now(), message=msg)
