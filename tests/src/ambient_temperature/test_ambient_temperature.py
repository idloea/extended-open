import unittest
import numpy as np
from src.ambient_temperature import UKData, MeteoNavarraData, get_ambient_temperature_in_degree_celsius_by_data_strategy
from src.read import read_case_data_from_yaml_file


class TestAmbientTemperature(unittest.TestCase):

    def test_UKData_get_ambient_temperature_in_degree_celsius(self):
        number_of_energy_management_system_time_intervals_per_day = 96
        ambient_temperature_in_degree_celsius = 20
        uk_data = UKData()
        result = uk_data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_system_time_intervals_per_day,
            predefined_ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius)
        expected_result = np.full(shape=96, fill_value=20)
        np.testing.assert_equal(expected_result, result)

    def test_MeteoNavarraData_get_ambient_temperature_in_degree_celsius(self):
        number_of_energy_management_system_time_intervals_per_day = 96
        file_path = 'tests/src/ambient_temperature/20220717_ambient_temperature_upna.csv'
        meteo_navarra_data = MeteoNavarraData()
        ambient_temperature_in_degree_celsius = meteo_navarra_data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_time_intervals_per_day=
            number_of_energy_management_system_time_intervals_per_day,
            file_path=file_path)
        result = ambient_temperature_in_degree_celsius[0:5]
        expected_result = np.array([20.05045488, 20.15392266, 19.02882983, 18.43678492, 17.87204455])
        np.testing.assert_array_almost_equal(expected_result, result)

    def test_get_ambient_temperature_in_degree_celsius_by_data_strategy_UK(self):
        file_path = 'tests/src/ambient_temperature'
        yaml_file = 'uk_summer_no_flexibility.yaml'
        case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
        number_of_energy_management_time_intervals_per_day = 96
        result = get_ambient_temperature_in_degree_celsius_by_data_strategy(
            case_data=case_data,
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day)
        shape = (number_of_energy_management_time_intervals_per_day,)
        expected_result = np.full(shape=shape, fill_value=22)
        np.testing.assert_equal(expected_result, result)

    def test_get_ambient_temperature_in_degree_celsius_by_data_strategy_MeteoNavarra(self):
        file_path = 'tests/src/ambient_temperature'
        yaml_file = 'pamplona_meteo_navarra.yaml'
        case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
        number_of_energy_management_time_intervals_per_day = 96
        ambient_temperature_in_degree_celsius = get_ambient_temperature_in_degree_celsius_by_data_strategy(
            case_data=case_data,
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day)
        result = ambient_temperature_in_degree_celsius[0:5]
        expected_result = np.array([20.05045488, 20.15392266, 19.02882983, 18.43678492, 17.87204455])
        np.testing.assert_almost_equal(expected_result, result)

    def test_get_ambient_temperature_in_degree_celsius_by_data_strategy_ValueError(self):
        file_path = 'tests/src/ambient_temperature'
        yaml_file = 'value_error.yaml'
        case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
        number_of_energy_management_time_intervals_per_day = 96
        with self.assertRaises(ValueError):
            get_ambient_temperature_in_degree_celsius_by_data_strategy(
                case_data=case_data,
                number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day)
