import unittest
import numpy as np
from typing import List

from src.markets import Market
from src.time_intervals import get_period_with_name_hour_and_euros_per_kilowatt_hour, \
    get_daily_periods_with_name_hour_and_euros_per_kilowatt_hour


def create_market(import_periods: List[dict]) -> Market:
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

    market = Market(network_bus_id=network_bus_id,
                    market_time_series_resolution_in_minutes=market_time_series_minute_resolution,
                    export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                    import_periods=import_periods,
                    max_demand_charge_in_euros_per_kWh=max_demand_charge_in_euros_per_kWh,
                    max_import_kilowatts=max_import_kilowatts,
                    max_export_kilowatts=max_export_kilowatts,
                    offered_kW_in_frequency_response=offered_kW_in_frequency_response,
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
        result = get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name=period_name,
                                                                       period_duration_in_hours=
                                                                       period_duration_in_hours,
                                                                       period_price_in_euros_per_kilowatt_hour=
                                                                       period_price_in_euros_per_kilowatt_hour)

        self.assertEqual(expected_result, result)

    def test_get_daily_periods_with_name_hour_and_euros_per_kilowatt_hour(self):
        period_one_name = 'peak'
        period_one_hours = 14
        period_one_euros_per_kilowatt_hour = 0.3
        period_two_name = 'valley'
        period_two_hours = 10
        period_two_euros_per_kilowatt_hour = 0.1

        period_one = get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name=period_one_name,
                                                                           period_duration_in_hours=period_one_hours,
                                                                           period_price_in_euros_per_kilowatt_hour=
                                                                           period_one_euros_per_kilowatt_hour)
        period_two = get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name=period_two_name,
                                                                           period_duration_in_hours=period_two_hours,
                                                                           period_price_in_euros_per_kilowatt_hour=
                                                                           period_two_euros_per_kilowatt_hour)
        periods = [period_one, period_two]
        result = get_daily_periods_with_name_hour_and_euros_per_kilowatt_hour(periods=periods)
        expected_result = [{'peak': [14, 0.3]}, {'valley': [10, 0.1]}]
        self.assertEqual(expected_result, result)

    def test_get_import_costs_in_euros_per_day_and_period(self):
        period_one_name = 'peak'
        period_one_hours = 14
        period_one_euros_per_kilowatt_hour = 1.0
        period_two_name = 'valley'
        period_two_hours = 10
        period_two_euros_per_kilowatt_hour = 2.0

        period_one = get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name=period_one_name,
                                                                           period_duration_in_hours=period_one_hours,
                                                                           period_price_in_euros_per_kilowatt_hour=
                                                                           period_one_euros_per_kilowatt_hour)
        period_two = get_period_with_name_hour_and_euros_per_kilowatt_hour(period_name=period_two_name,
                                                                           period_duration_in_hours=period_two_hours,
                                                                           period_price_in_euros_per_kilowatt_hour=
                                                                           period_two_euros_per_kilowatt_hour)
        import_periods = [period_one, period_two]
        test_market = create_market(import_periods=import_periods)
        result = test_market.get_import_costs_in_euros_per_day_and_period()
        first_array = np.ones(shape=14) * 1.0
        second_array = np.ones(shape=10) * 2.0
        expected_result = [first_array, second_array]
        np.testing.assert_equal(expected_result, result)
