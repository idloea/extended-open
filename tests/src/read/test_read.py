import unittest
import numpy as np
from datetime import datetime
import pandas as pd
from src.read import read_open_csv_files, read_preprocessing_meteo_navarra_ambient_temperature_csv_data, \
    get_import_period_prices_from_yaml, read_case_data_from_yaml_file, get_specific_import_price


class TestRead(unittest.TestCase):

    def test_read_open_csv_files(self) -> None:
        expected_result = [0.66400, 0.24700, 0.04800]

        path = 'tests/src/read'
        data = read_open_csv_files(path=path, csv_file='Loads_1min_2013JUN.csv')
        result = data[0][0:3]  # Get a sample
        np.testing.assert_almost_equal(expected_result, result)

    def test_read_meteo_navarra_ambient_temperature_csv_data(self) -> None:
        file_path = 'tests/src/read/20220717_ambient_temperature_upna.csv'
        result = read_preprocessing_meteo_navarra_ambient_temperature_csv_data(file_path).head()
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

    def test_get_import_period_prices_from_yaml(self) -> None:
        yaml_file = '01_january_no_flexibility.yaml'
        file_path = 'tests/src/read'
        case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
        result = get_import_period_prices_from_yaml(case_data)
        expected_result = {'P1': 0.1395,
                           'P2': 0.1278,
                           'P3': 0.1110,
                           'P4': 0.1014,
                           'P5': 0.0927,
                           'P6': 0.0871}
        self.assertEqual(expected_result, result)

    def test_get_import_price_for_specific_period(self) -> None:
        yaml_file = '01_january_no_flexibility.yaml'
        file_path = 'tests/src/read'
        case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
        period = 'P3'
        result = get_specific_import_price(case_data=case_data, period=period)
        expected_result = 0.1110
        self.assertEqual(expected_result, result)
