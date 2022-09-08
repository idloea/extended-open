import unittest
import numpy as np
from datetime import datetime
import pandas as pd
from src.read import read_open_csv_files, read_meteo_navarra_ambient_temperature_csv_data


class Read(unittest.TestCase):

    def test_read_open_csv_files(self):
        expected_result = [0.66400, 0.24700, 0.04800]

        path = 'tests/src/read'
        data = read_open_csv_files(path=path, csv_file='Loads_1min_2013JUN.csv')
        result = data[0][0:3]  # Get a sample
        np.testing.assert_almost_equal(expected_result, result)

    def test_read_meteo_navarra_ambient_temperature_csv_data(self):
        file_path = 'tests/src/read/20220717_ambient_temperature_upna.csv'
        result = read_meteo_navarra_ambient_temperature_csv_data(file_path).head()
        first_time_stamp = datetime(2022, 7, 17, 0, 0)
        second_time_stamp = datetime(2022, 7, 17, 0, 10)
        third_time_stamp = datetime(2022, 7, 17, 0, 20)
        fourth_time_stamp = datetime(2022, 7, 17, 0, 30)
        fifth_time_stamp = datetime(2022, 7, 17, 0, 40)
        date_times = [first_time_stamp, second_time_stamp, third_time_stamp, fourth_time_stamp, fifth_time_stamp]
        degree_celsius = [20.1, 20.3, 19.8, 19.0, 18.7]
        expected_dictionary = {'DateTime': date_times, 'DegreeCelsius': degree_celsius}
        expected_result = pd.DataFrame.from_dict(expected_dictionary)
        pd.testing.assert_frame_equal(expected_result, result)





