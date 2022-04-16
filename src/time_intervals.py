from typing import List


def get_number_of_time_intervals_per_day(time_series_resolution_in_hours: float) -> int:
    hours_per_day = 24
    return int(hours_per_day / time_series_resolution_in_hours)


def get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name: str, period_duration_in_hours: int,
                                                          period_price_in_euros_per_kilowatt_hour: float) -> dict:
    return {period_name: [period_duration_in_hours, period_price_in_euros_per_kilowatt_hour]}


def check_sum_of_daily_periods_in_hours_equals_twenty_four(periods: List[dict]):
    period_durations_in_hours = []
    for period in periods:
        period_duration = get_period_hours(period=period)
        period_durations_in_hours.append(period_duration)
    sum_period_durations_in_hours = sum(period_durations_in_hours)
    if sum_period_durations_in_hours != 24:
        raise ValueError('The sum of the current period durations in hours is {} and it must be 24')


def get_period_hours(period: dict) -> int:
    return list(period.values())[0][0]
