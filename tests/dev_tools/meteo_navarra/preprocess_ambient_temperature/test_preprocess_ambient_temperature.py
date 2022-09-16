import os
import unittest
from datetime import datetime
import pandas as pd
from dev_tools.meteo_navarra.preprocess_ambient_temperature import \
    adapt_ambient_temperature_data_from_solar_time_to_regular_time


class TestPreprocessAmbientTemperature(unittest.TestCase):

    def test_adapt_ambient_temperature_data_from_solar_time_to_regular_time(self):
        read_path = 'tests/dev_tools/meteo_navarra/preprocess_ambient_temperature'
        read_file = '202110_ambient_temperature.csv'
        start_date = '2021-10-15'
        end_date = '2021-10-16'
        time_schedule = 'summer'
        write_path = read_path
        adapt_ambient_temperature_data_from_solar_time_to_regular_time(read_path=read_path, read_file=read_file,
                                                                       time_schedule=time_schedule,
                                                                       start_date=start_date, end_date=end_date,
                                                                       write_path=write_path)
        file = '20211015_ambient_temperature_upna.csv'
        file_write_path = write_path + '/' + file
        data = pd.read_csv(filepath_or_buffer=file_write_path)
        data['DateTime'] = pd.to_datetime(data['DateTime'], format='%Y-%m-%d %H:%M:%S')
        result = data.head()
        first_time_stamp = datetime(2021, 10, 15, 0, 0)
        second_time_stamp = datetime(2021, 10, 15, 0, 10)
        third_time_stamp = datetime(2021, 10, 15, 0, 20)
        fourth_time_stamp = datetime(2021, 10, 15, 0, 30)
        fifth_time_stamp = datetime(2021, 10, 15, 0, 40)
        date_times = [first_time_stamp, second_time_stamp, third_time_stamp, fourth_time_stamp, fifth_time_stamp]
        degree_celsius = [6.6, 6.5, 6.7, 6.4, 6.7]
        expected_dictionary = {'DateTime': date_times, 'DegreeCelsius': degree_celsius}
        expected_result = pd.DataFrame.from_dict(expected_dictionary)
        pd.testing.assert_frame_equal(expected_result, result)
        os.remove(file_write_path)
        print(f'{file} has been removed successfully after passing the test')

    def test_adapt_ambient_temperature_data_from_solar_time_to_regular_time_empty(self):
        read_path = 'tests/dev_tools/meteo_navarra/preprocess_ambient_temperature'
        read_file = '202110_ambient_temperature.csv'
        start_date = '1999-10-15'
        end_date = '1999-10-16'
        time_schedule = 'summer'
        write_path = read_path
        with self.assertRaises(ValueError):
            adapt_ambient_temperature_data_from_solar_time_to_regular_time(read_path=read_path, read_file=read_file,
                                                                           time_schedule=time_schedule,
                                                                           start_date=start_date, end_date=end_date,
                                                                           write_path=write_path)
