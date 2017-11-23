import time
from pymongo import MongoClient

from core.models import PoloniexKey
from core.utils.BotConn import BotConn


def calculate_time(time_stamp: int):
    return time.time() - time_stamp


# КОСТЫЛЬ :))))000)
def perform_indicators_to_str(indicators):
    ret_list = list()
    str_args = str()
    for indicator in indicators:
        if indicator['indicator_name'] == 'rsi' or indicator['indicator_name'] == 'macd':
            indicator['name'] = indicator.pop('indicator_name')

        for arg in indicator['args']:
            str_args += '{}={}'.format(arg, str(indicator['args'][arg])) + ','

        ret_list.append([indicator['name'], str_args[:-1]])

    return ret_list


# ЕЩЕ ОДИН КОСТЫЛЬ :3
def perform_str_to_indicator(indicators):
    ret_list = list()
    try:
        for indicator in indicators:
            args_str = indicator[1].split(',')
            args_dict = dict()
            for arg in args_str:
                args_dict[arg.split('=')[0]] = float(arg.split('=')[1])

            if indicator[0] == 'rsi' or indicator[0] == 'macd':
                ret_list.append({'indicator_name': indicator[0], 'args': args_dict})
            else:
                ret_list.append({'indicator_name': 'ma', 'name': indicator[0], 'args': args_dict})
    except IndexError:
        ret_list = []

    return ret_list


def get_conn(url):
    return MongoClient(url).elbotesmio


def get_stock_exchange_params(stock_exchange: str, conn):
    currencies = list()
    for key in conn.get_currencies():
        currencies.append(key)

    ticks_temp = {'sec': list(), 'time': list()}

    if stock_exchange == 'poloniex':
        ticks_temp['sec'] = [300, 900, 1800, 7200, 14400, 86400]
        ticks_temp['time'] = ['5m', '15m', '30m', '2h', '4h', '1D']
    elif stock_exchange == 'bitfinex':
        ticks_temp['sec'] = [60, 300, 900, 1800, 3600, 10800, 21600, 43200, 86400]
        ticks_temp['time'] = ['1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D']
    elif stock_exchange == 'bittrex':
        ticks_temp['sec'] = [60, 300, 1800, 3600, 86400]
        ticks_temp['time'] = ['1m', '5m', '30m', '1h', '1D']

    ticks = list()
    for x in range(len(ticks_temp['sec'])):
        ticks.append({'time': ticks_temp['time'][x], 'sec': ticks_temp['sec'][x]})

    return {'ticks': ticks, 'currencies': currencies}


def get_key_and_secret(user, stock_exchange: str):
    if stock_exchange == BotConn.Poloniex:
        obj = PoloniexKey.objects.get(user=user.id)
        return obj.key, obj.secret
    elif stock_exchange == BotConn.Bitfinex: pass
        # obj = BitfinexKey.objects.get(user=user.id)
        # return obj.key, obj.secret
    elif stock_exchange == BotConn.Bittrex: pass
        # obj = Bittrex.objects.get(user=user.id)
        # return obj.key, obj.secret