import unittest
import datetime
import pandas as pd
from src.data_conversion import convert_10_min_data_to_1_min_data
from src.read import read_meteo_navarra_solar_radiation_data


class DataConversion(unittest.TestCase):

    def setUp(self):
        file_path = 'data/solar_radiation/pamplona/10_min/2021_2022_pamplona_upna_10_min_solar_radiation.xlsx'
        self.data = read_meteo_navarra_solar_radiation_data(file_path=file_path)

    def test_convert_10_min_data_to_1_min_data(self):
        data_with_1_min_frequency = convert_10_min_data_to_1_min_data(data=self.data)
        time_delta = pd.Timedelta(1, 'minute')
        data_with_1_min_frequency_index = data_with_1_min_frequency.index
        first_minute = data_with_1_min_frequency_index[0]
        second_minute = data_with_1_min_frequency_index[1]
        first_minute_delta = second_minute - first_minute
        last_minute = data_with_1_min_frequency_index[-1]
        second_last_minute = data_with_1_min_frequency_index[-2]
        last_minute_delta = last_minute - second_last_minute

        self.assertEqual(time_delta, first_minute_delta)
        self.assertEqual(time_delta, last_minute_delta)

    def test_convert_10_min_data_to_1_min_data_length(self):
        filtered_data = self.data[self.data['Date'] == '2021-01-07']
        data_1_min = convert_10_min_data_to_1_min_data(data=filtered_data)
        result = len(data_1_min)
        expected_result = 24 * 60
        self.assertEqual(expected_result, result)
