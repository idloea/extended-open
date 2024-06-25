import datetime
import unittest

import numpy as np

from src.time_intervals import get_number_of_time_intervals_per_day, \
    check_sum_of_daily_periods_in_hours_equals_twenty_four, check_unique_hours_of_daily_periods, \
    check_all_hours_of_daily_periods, get_range_array_from_between_hours


class TimeIntervals(unittest.TestCase):

    def test_get_number_of_time_intervals_per_day(self):
        expected_result = 12
        time_series_resolution_in_hours = 2
        result = get_number_of_time_intervals_per_day(time_series_resolution_in_hours=time_series_resolution_in_hours)
        self.assertEqual(expected_result, result)

    def test_check_sum_of_daily_periods_in_hours_equals_twenty_four(self):
        periods = {'P1': [9, 10, 11, 12, 13, 18, 19, 20, 21],
                   'P2': [8, 14, 15, 16, 17, 22, 23],
                   'P6': [0, 1, 2, 3, 4, 5, 6]}
        with self.assertRaises(ValueError):
            check_sum_of_daily_periods_in_hours_equals_twenty_four(periods=periods)

    def test_check_unique_hours_of_daily_periods(self):
        periods = {'P1': [9, 10, 11, 12, 13, 18, 19, 20, 21],
                   'P2': [9, 14, 15, 16, 17, 22, 23],
                   'P6': [0, 1, 2, 3, 4, 5, 6]}
        with self.assertRaises(ValueError):
            check_unique_hours_of_daily_periods(periods=periods)

    def test_check_all_hours_of_daily_periods(self):
        periods = {'P1': [9, 10, 11, 12, 13, 18, 19, 20, 21],
                   'P2': [8, 14, 15, 16, 17, 22, 23],
                   'P6': [0, 1, 2, 3, 4, 5, 6]}
        with self.assertRaises(ValueError):
            check_all_hours_of_daily_periods(periods=periods)

    def test_get_range_array_from_between_hours(self) -> None:
        start_time_in_hours = 11
        stop_time_in_hours = 12.5
        step_in_minutes = 15
        result = get_range_array_from_between_hours(start_time_in_hours=start_time_in_hours,
                                                    stop_time_in_hours=stop_time_in_hours,
                                                    step_in_minutes=step_in_minutes)
        expected_result = np.arange(44, 51, 1)
        np.testing.assert_array_equal(expected_result, result)
