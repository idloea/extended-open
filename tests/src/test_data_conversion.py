import unittest
import datetime
import pandas as pd

from src.data_conversion import convert_10_min_data_to_1_min_data


class DataConversion(unittest.TestCase):

    def test_convert_10_min_data_to_1_min_data(self):
        file_path = 'data/solar_radiation/pamplona/10_min/2021_2022_pamplona_upna_10_min_solar_radiation.xlsx'
        data = pd.read_excel(file_path, engine='openpyxl')
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data.sort_values(by=['Timestamp'], inplace=True)
        data['Date'] = data['Timestamp'].dt.to_period('D')
        data = data.set_index('Timestamp')
        result = convert_10_min_data_to_1_min_data(data=data)
        result_sample = result.sample(random_state=50)
        date_time_string = '2021-01-09 12:01:00'
        index = datetime.datetime.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')
        expected_data = {'Measured_radiation_W/m2': 117.4, 'Direct_radiation_W/m2': 1.3,
                         'Reflected_radiation_W/m2': 4.5, 'Diffused_radiation_W/m2': 101.4,
                         'Global_radiation_W/m2': 107.2, 'Date': datetime.datetime(2021, 1, 9)}
        expected_result = pd.DataFrame(data=expected_data, index=pd.Series(index))
        expected_result['Date'] = expected_result['Date'].dt.to_period('D')
        pd.testing.assert_frame_equal(expected_result, result_sample)
