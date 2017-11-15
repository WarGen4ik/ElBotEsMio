import time

MINUTE, HOUR, DAY = 60, 60 * 60, 60 * 60 * 24
WEEK, MONTH, YEAR = DAY * 7, DAY * 30, DAY * 365
FIVE_MIN, FIFTEEN_MIN, THIRTY_MIN = MINUTE * 5, MINUTE * 15, MINUTE * 30


def calculate_time(time_stamp: int):
    return time.time() - time_stamp