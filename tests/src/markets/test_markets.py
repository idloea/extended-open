import unittest
import numpy as np
from typing import List
from src.markets import Market, get_market, OPENMarket, SpanishMarket
from src.read import read_case_data_from_yaml_file


def create_open_market(import_periods: List[dict]) -> Market:
    network_bus_id = 1
    market_time_series_minute_resolution = 1
    export_prices_in_euros_per_kilowatt_hour = 0.2
    max_demand_charge_in_euros_per_kWh = 0.12
    max_import_kilowatts = 500
    max_export_kilowatts = 500
    offered_kW_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0.6
    min_frequency_response_state_of_charge = 0.4
    frequency_response_price_in_euros_per_kilowatt_hour = 0.4

    market = OPENMarket(network_bus_id=network_bus_id,
                        market_time_series_resolution_in_hours=market_time_series_minute_resolution,
                        export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                        import_periods=import_periods,
                        max_demand_charge_in_euros_per_kilowatt_hour=max_demand_charge_in_euros_per_kWh,
                        max_import_kilowatts=max_import_kilowatts, max_export_kilowatts=max_export_kilowatts,
                        offered_kilowatt_in_frequency_response=offered_kW_in_frequency_response,
                        max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                        min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                        frequency_response_price_in_euros_per_kilowatt_hour=
                        frequency_response_price_in_euros_per_kilowatt_hour)

    return market


def create_spanish_market(yaml_file: str, file_path: str) -> Market:
    import_periods = {'P1': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
                      'P2': [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21],
                      'P3': [23]}
    network_bus_id = 1
    market_time_series_resolution_in_hours = 1
    export_prices_in_euros_per_kilowatt_hour = 0
    import_period_prices = {'P1': 1,
                            'P2': 2,
                            'P3': 3}
    max_demand_charge_in_euros_per_kilowatt_hour = 0.5
    max_import_kilowatts = 500
    max_export_kilowatts = 500
    offered_kilowatt_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0
    min_frequency_response_state_of_charge = 0
    frequency_response_price_in_euros_per_kilowatt_hour = 1
    case_data = read_case_data_from_yaml_file(cases_file_path=file_path, file_name=yaml_file)
    market = get_market(case_data=case_data,
                        import_period_prices=import_period_prices,
                        network_bus_id=network_bus_id,
                        market_time_series_resolution_in_hours=market_time_series_resolution_in_hours,
                        export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                        import_periods=import_periods,
                        max_demand_charge_in_euros_per_kilowatt_hour=max_demand_charge_in_euros_per_kilowatt_hour,
                        max_import_kilowatts=max_import_kilowatts,
                        max_export_kilowatts=max_export_kilowatts,
                        offered_kilowatt_in_frequency_response=offered_kilowatt_in_frequency_response,
                        max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                        min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                        frequency_response_price_in_euros_per_kilowatt_hour=
                        frequency_response_price_in_euros_per_kilowatt_hour)
    return market


class TestMarkets(unittest.TestCase):

    def test_get_period_with_name_hour_and_euros_per_kilowatt_hour(self):
        period_name = 'peak'
        period_duration_in_hours = 7
        period_price_in_euros_per_kilowatt_hour = 0.3

        expected_result = {'peak': [7, 0.3]}
        result = {period_name: [period_duration_in_hours, period_price_in_euros_per_kilowatt_hour]}

        self.assertEqual(expected_result, result)

    def test_get_market_open(self):
        yaml_file = 'open_market.yaml'
        file_path = 'tests/src/markets'
        import_period_prices = {'P1': 1, 'P2': 2}
        network_bus_id = 1
        market_time_series_resolution_in_hours = 1
        export_prices_in_euros_per_kilowatt_hour = 0
        import_periods = [{'peak': [7, 0.083]}, {'valley': [17, 0.18]}]
        max_demand_charge_in_euros_per_kilowatt_hour = 0.5
        max_import_kilowatts = 500
        max_export_kilowatts = 500
        offered_kilowatt_in_frequency_response = 0
        max_frequency_response_state_of_charge = 0
        min_frequency_response_state_of_charge = 0
        frequency_response_price_in_euros_per_kilowatt_hour = 1
        case_data = read_case_data_from_yaml_file(cases_file_path=file_path, file_name=yaml_file)
        market = get_market(case_data=case_data,
                            import_period_prices=import_period_prices,
                            network_bus_id=network_bus_id,
                            market_time_series_resolution_in_hours=market_time_series_resolution_in_hours,
                            export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                            import_periods=import_periods,
                            max_demand_charge_in_euros_per_kilowatt_hour=max_demand_charge_in_euros_per_kilowatt_hour,
                            max_import_kilowatts=max_import_kilowatts,
                            max_export_kilowatts=max_export_kilowatts,
                            offered_kilowatt_in_frequency_response=offered_kilowatt_in_frequency_response,
                            max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                            min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                            frequency_response_price_in_euros_per_kilowatt_hour=
                            frequency_response_price_in_euros_per_kilowatt_hour)
        result = isinstance(market, OPENMarket)
        expected_result = True
        self.assertEqual(expected_result, result)

    def test_get_import_costs_in_euros_per_day_and_period_open(self):
        import_periods = [{'peak': [14, 1.0]}, {'valley': [10, 2.0]}]
        open_market = create_open_market(import_periods=import_periods)
        result = open_market.get_import_costs_in_euros_per_day_and_period()
        first_array = np.ones(shape=14) * 1.0
        second_array = np.ones(shape=10) * 2.0
        expected_result = np.hstack(np.array([first_array, second_array]))
        np.testing.assert_equal(expected_result, result)

    def test_get_market_spanish(self):
        yaml_file = 'spanish_market.yaml'
        file_path = 'tests/src/markets'
        market = create_spanish_market(yaml_file=yaml_file, file_path=file_path)
        result = isinstance(market, SpanishMarket)
        expected_result = True
        self.assertEqual(expected_result, result)

    def test_get_import_costs_in_euros_per_day_and_period_spanish(self):
        yaml_file = 'spanish_market.yaml'
        file_path = 'tests/src/markets'
        market = create_spanish_market(yaml_file=yaml_file, file_path=file_path)
        result = market.get_import_costs_in_euros_per_day_and_period()
        expected_result = np.array([1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 3])
        np.testing.assert_equal(expected_result, result)

    def test_get_market_incorrect(self):
        yaml_file = 'incorrect_market.yaml'
        file_path = 'tests/src/markets'
        import_period_prices = {'P1': 1, 'P2': 2}
        network_bus_id = 1
        market_time_series_resolution_in_hours = 1
        export_prices_in_euros_per_kilowatt_hour = 0
        import_periods = [{'peak': [7, 0.083]}, {'valley': [17, 0.18]}]
        max_demand_charge_in_euros_per_kilowatt_hour = 0.5
        max_import_kilowatts = 500
        max_export_kilowatts = 500
        offered_kilowatt_in_frequency_response = 0
        max_frequency_response_state_of_charge = 0
        min_frequency_response_state_of_charge = 0
        frequency_response_price_in_euros_per_kilowatt_hour = 1
        case_data = read_case_data_from_yaml_file(cases_file_path=file_path, file_name=yaml_file)
        with self.assertRaises(ValueError):
            get_market(case_data=case_data,
                       import_period_prices=import_period_prices,
                       network_bus_id=network_bus_id,
                       market_time_series_resolution_in_hours=market_time_series_resolution_in_hours,
                       export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                       import_periods=import_periods,
                       max_demand_charge_in_euros_per_kilowatt_hour=max_demand_charge_in_euros_per_kilowatt_hour,
                       max_import_kilowatts=max_import_kilowatts,
                       max_export_kilowatts=max_export_kilowatts,
                       offered_kilowatt_in_frequency_response=offered_kilowatt_in_frequency_response,
                       max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                       min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                       frequency_response_price_in_euros_per_kilowatt_hour=
                       frequency_response_price_in_euros_per_kilowatt_hour)
