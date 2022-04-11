import unittest
from src.time_intervals import get_number_of_time_intervals_per_day, get_period_hours, get_period_cost_per_hour


class TimeIntervals(unittest.TestCase):

    def test_get_number_of_time_intervals_per_day(self):
        expected_result = 12
        time_series_resolution_in_hours = 2
        result = get_number_of_time_intervals_per_day(time_series_resolution_in_hours=time_series_resolution_in_hours)
        self.assertEqual(expected_result, result)

    def test_get_period_hours(self):
        period_name = 'peak'
        period_duration_in_hours = 7
        period_price_in_euros_per_kilowatt_hour = 0.3
        period = {period_name: [period_duration_in_hours, period_price_in_euros_per_kilowatt_hour]}
        expected_result = 7
        result = get_period_hours(period=period)
        self.assertEqual(expected_result, result)

    def test_get_period_cost_per_hour(self):
        period_name = 'peak'
        period_duration_in_hours = 7
        period_price_in_euros_per_kilowatt_hour = 0.3
        period = {period_name: [period_duration_in_hours, period_price_in_euros_per_kilowatt_hour]}
        expected_result = 0.3
        result = get_period_cost_per_hour(period=period)
        self.assertEqual(expected_result, result)
