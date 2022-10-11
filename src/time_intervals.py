from typing import List
import numpy as np


def get_number_of_time_intervals_per_day(time_series_resolution_in_hours: float) -> int:
    hours_per_day = 24
    return int(hours_per_day / time_series_resolution_in_hours)


def check_sum_of_daily_periods_in_hours_equals_twenty_four(periods: dict) -> None:
    period_durations_in_hours = []
    for period_name, period_hours in periods.items():
        period_hours_length = len(period_hours)
        period_durations_in_hours.append(period_hours_length)
    sum_period_durations_in_hours = sum(period_durations_in_hours)
    if sum_period_durations_in_hours != 24:
        raise ValueError(
            f'The sum of the current period durations in hours is {sum_period_durations_in_hours} and it must be 24')


def check_unique_hours_of_daily_periods(periods: dict) -> None:
    period_hours_list = []
    for period_name, period_hours in periods.items():
        period_hours_list.append(period_hours)
    flattened_period_hours_list = [value for sublist in period_hours_list for value in sublist]
    flag = len(set(flattened_period_hours_list)) == len(flattened_period_hours_list)
    if not flag:
        raise ValueError('There is at least one duplicated hour in the import period')


def check_all_hours_of_daily_periods(periods: dict) -> None:
    period_hours_list = []
    for period_name, period_hours in periods.items():
        period_hours_list.append(period_hours)
    flattened_period_hours_list = [value for sublist in period_hours_list for value in sublist]
    sorted_period_hours_list = np.array(sorted(flattened_period_hours_list))
    hours_list = np.arange(0, 24, 1)
    length_sorted_period_hours_list = len(sorted_period_hours_list)
    length_hours_list = len(hours_list)
    if length_hours_list != length_sorted_period_hours_list:
        raise ValueError('There is at least one missing hour in the import period')
