import unittest
from pathlib import Path
import pandas as pd
import pandas.testing

from dev_tools.result_format import get_dataframe_from_directory_with_json_files, gather_all_input_and_output_results


class TestResultFormat(unittest.TestCase):
    def test_get_dataframe_from_directory_with_json_files(self) -> None:
        path_string = 'tests/dev_tools/result_format/data'
        results_directory = Path(path_string)
        json_file_name = 'input_case_data.json'
        result = get_dataframe_from_directory_with_json_files(directory=results_directory,
                                                              json_file_name=json_file_name)
        first_row = {'rated_photovoltaic_kilowatts': 400,
                     'simulation_time_series_resolution_in_minutes': 1,
                     'energy_management_system_time_series_resolution_in_minutes': 15,
                     'number_of_electric_vehicles': 120,
                     'max_battery_capacity_in_kilowatts_per_hour': 30,
                     'max_battery_charging_power_in_kilowatts': 7,
                     'electric_vehicle_arrival_time_start': 12,
                     'electric_vehicle_arrival_time_end': 22,
                     'electric_vehicle_departure_time_start': 5,
                     'electric_vehicle_departure_time_end': 8,
                     'max_inside_degree_celsius': 25,
                     'min_inside_degree_celsius': 21,
                     'initial_inside_degree_celsius': 21,
                     'max_consumed_electric_heating_kilowatts': 400,
                     'max_consumed_electric_cooling_kilowatts': 400,
                     'heat_pump_coefficient_of_performance': 3,
                     'chiller_coefficient_of_performance': 1,
                     'building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius': 500,
                     'building_thermal_resistance_in_degree_celsius_per_kilowatts': 0.0337,
                     'export_prices_in_euros_per_kilowatt_hour': 0.189,
                     'demand_charge_in_euros_per_kilowatt': 0,
                     'max_import_kilowatts': 500,
                     'max_export_kilowatts': -500,
                     'offered_kilowatts_in_frequency_response': 0,
                     'max_frequency_response_state_of_charge': 0.6,
                     'min_frequency_response_state_of_charge': 0.4,
                     'frequency_response_price_in_euros_per_kilowatt_hour': 0.0059,
                     'grid_1_voltage_level_in_kilo_volts': 20,
                     'grid_2_voltage_level_in_kilo_volts': 0.4,
                     'grid_3_voltage_level_in_kilo_volts': 0.4,
                     'transformer_apparent_power_in_mega_volt_ampere': 0.4,
                     'length_from_bus_2_to_bus_3_in_km': 0.1,
                     'photovoltaic_generation_data_file_path': 'data/solar_radiation/pamplona/1_min/2022-01-01_pamplona.csv',
                     'electric_load_data_file_path': 'data/electric_loads/considered_building_types',
                     'data_strategy': 'MeteoNavarra',
                     'ambient_temperature_file_path': 'data/ambient_temperature/pamplona/20220115_ambient_temperature_upna.csv',
                     'market': 'Spanish',
                     'import_period_prices.P1': 0.1395,
                     'import_period_prices.P2': 0.1278,
                     'import_period_prices.P3': 0.111,
                     'import_period_prices.P4': 0.1014,
                     'import_period_prices.P5': 0.0927,
                     'import_period_prices.P6': 0.0871,
                     'FolderName': '20221230-122143_Commercial-275-bed Hospital.csv'}
        second_row = {'rated_photovoltaic_kilowatts': 400,
                      'simulation_time_series_resolution_in_minutes': 1,
                      'energy_management_system_time_series_resolution_in_minutes': 15,
                      'number_of_electric_vehicles': 120,
                      'max_battery_capacity_in_kilowatts_per_hour': 30,
                      'max_battery_charging_power_in_kilowatts': 7,
                      'electric_vehicle_arrival_time_start': 12,
                      'electric_vehicle_arrival_time_end': 22,
                      'electric_vehicle_departure_time_start': 5,
                      'electric_vehicle_departure_time_end': 8,
                      'max_inside_degree_celsius': 25,
                      'min_inside_degree_celsius': 21,
                      'initial_inside_degree_celsius': 21,
                      'max_consumed_electric_heating_kilowatts': 400,
                      'max_consumed_electric_cooling_kilowatts': 400,
                      'heat_pump_coefficient_of_performance': 3,
                      'chiller_coefficient_of_performance': 1,
                      'building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius': 500,
                      'building_thermal_resistance_in_degree_celsius_per_kilowatts': 0.0337,
                      'export_prices_in_euros_per_kilowatt_hour': 0.189,
                      'demand_charge_in_euros_per_kilowatt': 0,
                      'max_import_kilowatts': 500,
                      'max_export_kilowatts': -500,
                      'offered_kilowatts_in_frequency_response': 0,
                      'max_frequency_response_state_of_charge': 0.6,
                      'min_frequency_response_state_of_charge': 0.4,
                      'frequency_response_price_in_euros_per_kilowatt_hour': 0.0059,
                      'grid_1_voltage_level_in_kilo_volts': 20,
                      'grid_2_voltage_level_in_kilo_volts': 0.4,
                      'grid_3_voltage_level_in_kilo_volts': 0.4,
                      'transformer_apparent_power_in_mega_volt_ampere': 0.4,
                      'length_from_bus_2_to_bus_3_in_km': 0.1,
                      'photovoltaic_generation_data_file_path': 'data/solar_radiation/pamplona/1_min/2022-01-04_pamplona.csv',
                      'electric_load_data_file_path': 'data/electric_loads/considered_building_types',
                      'data_strategy': 'MeteoNavarra',
                      'ambient_temperature_file_path': 'data/ambient_temperature/pamplona/20220415_ambient_temperature_upna.csv',
                      'market': 'Spanish',
                      'import_period_prices.P1': 0.1395,
                      'import_period_prices.P2': 0.1278,
                      'import_period_prices.P3': 0.111,
                      'import_period_prices.P4': 0.1014,
                      'import_period_prices.P5': 0.0927,
                      'import_period_prices.P6': 0.0871,
                      'FolderName': '20221230-143502_Commercial-Office.csv'}
        expected_result = pd.DataFrame([first_row, second_row])
        pandas.testing.assert_frame_equal(expected_result, result)

    @unittest.skip
    def test_gather_all_input_and_output_results(self) -> None:
        directory_string = 'tests/dev_tools/result_format/data'
        directory = Path(directory_string)
        input_json_file_name = 'input_case_data.json'
        output_json_file_name = 'output_case_data.json'
        result = gather_all_input_and_output_results(directory=directory, input_json_file_name=input_json_file_name,
                                                     output_json_file_name=output_json_file_name)
        print('hi')
        # TODO: add the expected result (dataframe)
