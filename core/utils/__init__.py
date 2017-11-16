import time

MINUTE, HOUR, DAY = 60, 60 * 60, 60 * 60 * 24
WEEK, MONTH, YEAR = DAY * 7, DAY * 30, DAY * 365
FIVE_MIN, FIFTEEN_MIN, THIRTY_MIN = MINUTE * 5, MINUTE * 15, MINUTE * 30


def calculate_time(time_stamp: int):
    return time.time() - time_stamp


# КОСТЫЛЬ :))))000)
def perform_indicators_to_str(indicators):
    ret_list = list()
    str_args = str()
    for indicator in indicators:
        for arg in indicator['args']:
            str_args += '{}={}'.format(arg, str(indicator['args'][arg])) + ','

        ret_list.append([indicator['name'], str_args[:-1]])

    return ret_list


# ЕЩЕ ОДИН КОСТЫЛЬ :3
def perform_str_to_indicator(indicators):
    ret_list = list()
    for indicator in indicators:
        args_str = indicator[1].split(',')
        args_dict = dict()
        for arg in args_str:
            args_dict[arg.split('=')[0]] = float(arg.split('=')[1])
        ret_list.append({'name': indicator[0], 'args': args_dict})

    return ret_list
