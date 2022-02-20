import unittest
from src.time_intervals import get_number_of_time_intervals_per_day


class TimeIntervals(unittest.TestCase):

    def test_get_number_of_time_intervals_per_day(self):
        expected_result = 12
        time_series_hour_resolution = 2
        result = get_number_of_time_intervals_per_day(time_series_hour_resolution=time_series_hour_resolution)
        self.assertEqual(expected_result, result)
