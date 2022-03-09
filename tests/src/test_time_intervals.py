import unittest
from src.time_intervals import get_number_of_time_intervals_per_day


class TimeIntervals(unittest.TestCase):

    def test_get_number_of_time_intervals_per_day(self):
        expected_result = 12
        time_series_resolution_in_hours = 2
        result = get_number_of_time_intervals_per_day(time_series_resolution_in_hours=time_series_resolution_in_hours)
        self.assertEqual(expected_result, result)
