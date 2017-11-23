from BotsConnections.poloniexConn import Poloniex, PoloniexError
from BotsConnections.Bittrex import Bittrex, BittrexError
from BotsConnections.Bitfinex import PublicV2, Trading_v2, TradingV1, BitfinexError

import datetime
import time as t

# for bittrex candles
from core.utils import candle_times

PROTECTION_PUB = 'pub'  # public methods
API_V2_0 = 'v2.0'


class BotException(Exception):
    pass


class BotConn:
    Poloniex = 'poloniex'
    Bitfinex = 'bitfinex'
    Bittrex = 'bittrex'

    def __init__(self, stock_exchange, key='', secret=''):
        self.key = key
        self.secret = secret
        self.stock_exchange = stock_exchange
        if stock_exchange == self.Poloniex:
            self.conn = Poloniex(key, secret)
        elif stock_exchange == self.Bittrex:
            self.conn = Bittrex(key, secret)
        elif stock_exchange == self.Bitfinex:
            self.conn1 = TradingV1(key, secret)  # для торговых запросов
            self.conn = Trading_v2(key, secret)  # для других торговых запросов
            self.publ_conn = PublicV2()  # для публичных запросов

    # нет медода для всех валют в биттрексе и битфинексе
    def get_ticker(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnTicker()
        elif self.stock_exchange == self.Bitfinex:
            return self.publ_conn.ticker()

    # done bittr bitf
    def get_ticker_pair(self, pair):
        try:  # raice exception for bot (magick)
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnTicker()[pair]
            elif self.stock_exchange == self.Bittrex:
                # форматирование вывода под вид полоникса
                formt = self.conn.query('getticker', {'market': pair.replace('_', '-')})
                if formt == 'INVALID_MARKET':
                    raise BittrexError('INVALID_MARKET')

                return {'last': formt['Bid'], 'lowestAsk': formt['Ask'], 'highestBid': formt['Last']}
            elif self.stock_exchange == self.Bitfinex:
                pair = 't' + pair.replace('_', '')
                res = self.publ_conn.ticker_pair(
                    pair)  # предположительно BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_PERK, LAST_PRICE, VOLUME, HIGH, LOW
                result = {'last': res[6], 'lowestAsk': res[2], 'highestBid': res[0]}
                return result

        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))
        except IndexError as ex:
            raise BotException('INVALID_MARKET')

    # skip
    def get_24h_volume(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.return24hVolume()

    # done bittr bitf
    def get_order_book(self, pair='all', depth=20):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnOrderBook(pair, depth)
            elif self.stock_exchange == self.Bittrex:
                source = self.conn.query('getorderbook',
                                         {'market': pair.replace('_', '-'), 'type': 'both', 'depth': depth})
                result = {'asks': [], 'bids': []}
                for i in range(len(source['buy'])):
                    result['bids'].append([source['buy'][i]['Rate'], source['buy'][i]['Quantity']])
                    result['asks'].append([source['sell'][i]['Rate'], source['sell'][i]['Quantity']])
                return result
            elif self.stock_exchange == self.Bitfinex:
                pair = 't' + pair.replace('_', '')
                depth = 'P3'  # P0, P1, P2, P3, R0
                res = self.publ_conn.books(pair, depth)
                result = {'asks': [], 'bids': []}
                for x in res:
                    if x[2] > 0:
                        result['asks'].append([x[0], x[2]])
                    elif x[2] < 0:
                        result['bids'].append([x[0], x[2]])
                return result
        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))

    def get_curr_bid_price(self, pair):
        return float(self.get_ticker_pair(pair)['highestBid'])

    def get_curr_ask_price(self, pair):
        return float(self.get_ticker_pair(pair)['lowestAsk'])

    # done bittr bitf
    def get_currencies(self):
        if self.stock_exchange == self.Poloniex:
            return self.conn.returnCurrencies()
        elif self.stock_exchange == self.Bittrex:
            source = self.conn.query('getcurrencies')  # все валюты с биттрекса без форматирования
            result = {}  # сюда пишутся словари с данными для каждой валюты

            for currency in source:  # приходиь list в которов один dict. переборєлементов этого dict
                result[currency['Currency']] = dict()
                result[currency['Currency']]['name'] = currency['CurrencyLong']
                result[currency['Currency']]['txFee'] = currency['TxFee']
                result[currency['Currency']]['minConf'] = currency['MinConfirmation']

                if currency['IsActive'] is True:
                    result[currency['Currency']]['frozen'] = 0
                elif currency['IsActive'] is True:
                    result[currency['Currency']]['frozen'] = 1
            return result
        elif self.stock_exchange == self.Bitfinex:  # возвращает только txFee для всех валют
            # res = self.conn1.account_fees()
            # result = {}
            # for key in res['withdraw']:
            #     result[key] = {'txFee': res['withdraw'][key]}
            # return result
            res = self.publ_conn.symbols()
            result = []
            for i in res:
                x = i[:3].upper()
                y = i[3:].upper()
                if x not in result:
                    result.append(x)
                if y not in result:
                    result.append(y)
            return result

    # done bittrex bitfinex
    def get_candle_info(self, pair: str, time=300, start=candle_times.DAY):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnChartData(pair, time, start)
            elif self.stock_exchange == self.Bittrex:
                # в битрексе есть еще oneMin, hour
                # биттрекс не возвращает аналога weightedAverage, как в полониксе
                if time == 300:
                    time = 'fiveMin'
                elif time == 1800:
                    time = 'thirtyMin'
                elif time == 86400:
                    time = 'Day'

                source = self.conn.query_v2('GetTicks', {
                    'marketName': pair.replace('_', '-'), 'tickInterval': time
                })

                result = []

                for x in source:
                    date = datetime.datetime.strptime(x['T'], '%Y-%m-%dT%H:%M:%S')
                    unixtime = int(t.mktime(date.timetuple()))
                    temp = {'date': unixtime, 'high': x['H'], 'low': x['L'], 'open': x['O'], 'close': x['C'],
                            'volume': x['BV'], 'quoteVolume': x['V']}
                    result.append(temp)
                return result
            elif self.stock_exchange == self.Bitfinex:
                pair = 't' + pair.replace('_', '')

                if time == 300:  # '1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '7D', '14D', '1M'
                    time = '5m'
                elif time == 900:
                    time = '5m'
                elif time == 1800:
                    time = '30m'
                elif time == 86400:
                    time = '1D'

                section = 'hist'  # "last", "hist"

                res = self.publ_conn.candles(time, pair, section)
                result = []
                for x in res:
                    result.append(
                        {'date': x[0], 'high': x[3], 'low': x[4], 'open': x[1], 'close': x[2], 'volume': x[5]})
                return result
        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))

    # done bittrex bitfinex
    def get_balances(self):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnBalances()
            elif self.stock_exchange == self.Bittrex:
                return self.conn.query('getbalances')
            elif self.stock_exchange == self.Bitfinex:
                return self.conn1.balances()
        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))

    def get_balance(self, currency: str):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnBalances()[currency]
            elif self.stock_exchange == self.Bittrex:
                return self.conn.query('getbalances')[currency]
            elif self.stock_exchange == self.Bitfinex:
                return self.conn1.balances()[currency]
        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))


    # bittrex_trouble, bitfinex done?
    def get_open_orders(self, pair='all'):
        try:
            if self.stock_exchange == self.Poloniex:
                return self.conn.returnOpenOrders(pair)
            elif self.stock_exchange == self.Bittrex:  # не может выводить ордеры на все валюты сразу
                return self.conn.query('getopenorders', {'market': pair.replace('_', '-')})

            # возвращает все открытые ордеры, не может выводить конкретную пару
            # нужно посмотреть как выводится список ордеров чтоб вытянуть конкретную пару
            elif self.stock_exchange == self.Bitfinex:
                pair = 't' + pair.replace('_', '')
                return self.conn.active_orders()
        except (PoloniexError, BittrexError, BitfinexError) as ex:
            raise BotException(str(ex))

    def is_any_open_order(self, pair):
        if self.stock_exchange == self.Poloniex:
            if self.conn.returnOpenOrders(pair):
                return True
            else:
                return False

    # done bittrex bitfinex ?
    def buy(self, pair: str, price: float, amount: float):
        if self.stock_exchange == self.Poloniex:
            return self.conn.buy(pair, price, amount)
        elif self.stock_exchange == self.Bittrex:
            return self.conn.query('buylimit', {'market': pair.replace('_', '-'), 'quantity': amount, 'rate': price})
        elif self.stock_exchange == self.Bitfinex:
            pair = 't' + pair.replace('_', '')
            side = 'buy'
            type_ = 'market'
            return self.conn1.new_order(self, pair, amount, price, side, type_, exchange='bitfinex',
                                        use_all_available=False)

    # done bittrex bitfinex ?
    def sell(self, pair: str, price: float, amount: float):
        if self.stock_exchange == self.Poloniex:
            return self.conn.sell(pair, price, amount)
        elif self.stock_exchange == self.Bittrex:
            return self.conn.query('selllimit', {'market': pair.replace('_', '-'), 'quantity': amount, 'rate': price})
        elif self.stock_exchange == self.Bitfinex:
            pair = 't' + pair.replace('_', '')
            side = 'sell'
            type_ = 'market'
            return self.conn1.new_order(self, pair, amount, price, side, type_, exchange='bitfinex',
                                        use_all_available=False)

    # done bittrex bitfinex ?
    def cancel_order(self, order_id: int):
        if self.stock_exchange == self.Poloniex:
            return self.conn.cancelOrder(order_id)
        elif self.stock_exchange == self.Bittrex:
            return self.conn.query('cancel', {'uuid': order_id})
        elif self.stock_exchange == self.Bitfinex:
            return self.conn1.cancel_order(order_id)


if __name__ == '__main__':
    p = BotConn('bitfinex', 'F4AC1AI7-JAHWF8C6-0142HBVX-J3WEKLZQ', '948c0bd67c9f673e5eb6610348d8773537e3ad36c59028a36f5aea6b344bfcd3d21645869cbc46dea4f5ce766756bd2b9bf954ba8a5cbe0ec47f0be907d941fd')
    print(p.get_ticker_pair('BTC_USD'))
