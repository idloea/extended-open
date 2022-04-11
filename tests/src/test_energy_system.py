import unittest
import numpy as np
import picos as pic
from typing import List, Optional
from src.assets import NonDispatchableAsset, StorageAsset, BuildingAsset
from src.energy_system import EnergySystem, get_temperature_constraint_for_no_initial_time
from src.markets import Market
from src.network_3_phase_pf import ThreePhaseNetwork


def _create_a_non_dispatchable_test_asset(active_power_in_kilowatts: np.ndarray,
                                          reactive_power_in_kilovolt_ampere_reactive:
                                          np.ndarray) -> NonDispatchableAsset:
    simulation_time_series_hour_resolution = 0.1
    bus_id = 1
    non_dispatchable_asset = NonDispatchableAsset(simulation_time_series_hour_resolution=
                                                  simulation_time_series_hour_resolution,
                                                  bus_id=bus_id, active_power_in_kilowatts=active_power_in_kilowatts,
                                                  reactive_power_in_kilovolt_ampere_reactive=
                                                  reactive_power_in_kilovolt_ampere_reactive)

    return non_dispatchable_asset


def _create_a_test_storage_asset() -> List[StorageAsset]:
    max_energy_in_kilowatt_hour = np.array([10, 10, 10])
    min_energy_in_kilowatt_hour = np.array([1, 1, 1])
    max_active_power_in_kilowatts = np.array([10, 10, 10])
    min_active_power_in_kilowatts = np.array([1, 1, 1])
    initial_energy_level_in_kilowatt_hour = 0.5
    required_terminal_energy_level_in_kilowatt_hour = 5.5
    bus_id = 1
    simulation_time_series_hour_resolution = 0.1
    number_of_time_intervals_per_day = 10
    energy_management_system_time_series_resolution_in_seconds = 0.2
    number_of_energy_management_system_time_intervals_per_day = 5

    storage_asset = StorageAsset(max_energy_in_kilowatt_hour=max_energy_in_kilowatt_hour,
                                 min_energy_in_kilowatt_hour=min_energy_in_kilowatt_hour,
                                 max_active_power_in_kilowatts=max_active_power_in_kilowatts,
                                 min_active_power_in_kilowatts=min_active_power_in_kilowatts,
                                 initial_energy_level_in_kilowatt_hour=initial_energy_level_in_kilowatt_hour,
                                 required_terminal_energy_level_in_kilowatt_hour=
                                 required_terminal_energy_level_in_kilowatt_hour,
                                 bus_id=bus_id,
                                 simulation_time_series_hour_resolution=simulation_time_series_hour_resolution,
                                 number_of_time_intervals_per_day=number_of_time_intervals_per_day,
                                 energy_management_system_time_series_resolution_in_seconds=
                                 energy_management_system_time_series_resolution_in_seconds,
                                 number_of_energy_management_system_time_intervals_per_day=
                                 number_of_energy_management_system_time_intervals_per_day)

    return [storage_asset]


def _create_a_test_network() -> ThreePhaseNetwork:
    return ThreePhaseNetwork()


def _create_a_test_market() -> Market:
    network_bus_id = 1
    market_time_series_minute_resolution = 0.1
    export_prices_in_euros_per_kilowatt_hour = 5.5
    period_one_name = 'peak'
    period_one_hours = 20
    period_one_euros_per_kilowatt_hour = 10.5
    period_two_name = 'valley'
    period_two_hours = 4
    period_two_euros_per_kilowatt_hour = 3.5
    import_periods = [{period_one_name: [period_one_hours, period_one_euros_per_kilowatt_hour]},
                      {period_two_name: [period_two_hours, period_two_euros_per_kilowatt_hour]}]

    max_demand_charge_in_euros_per_kWh = 20.5
    max_import_kilowatts = 500
    max_export_kilowatts = 500
    offered_kW_in_frequency_response = 0
    max_frequency_response_state_of_charge = 1
    min_frequency_response_state_of_charge = 0
    frequency_response_price_in_euros_per_kilowatt_hour = 7.5
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


def _create_a_test_building_asset() -> List[BuildingAsset]:
    max_inside_degree_celsius = 22
    min_inside_degree_celsius = 15
    max_consumed_electric_heating_kilowatts = 500
    max_consumed_electric_cooling_kilowatts = 500
    initial_inside_degree_celsius = 17
    building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = 5.5
    building_thermal_resistance_in_degree_celsius_per_kilowatts = 4.5
    heat_pump_coefficient_of_performance = 3
    chiller_coefficient_of_performance = 2
    ambient_degree_celsius = 19
    bus_id = 1
    simulation_time_series_hour_resolution = 0.1
    energy_management_system_time_series_resolution_in_hours = 0.2
    building_asset = BuildingAsset(max_inside_degree_celsius=max_inside_degree_celsius,
                                   min_inside_degree_celsius=min_inside_degree_celsius,
                                   max_consumed_electric_heating_kilowatts=max_consumed_electric_heating_kilowatts,
                                   max_consumed_electric_cooling_kilowatts=max_consumed_electric_cooling_kilowatts,
                                   initial_inside_degree_celsius=initial_inside_degree_celsius,
                                   building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius=
                                   building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius,
                                   building_thermal_resistance_in_degree_celsius_per_kilowatts=
                                   building_thermal_resistance_in_degree_celsius_per_kilowatts,
                                   heat_pump_coefficient_of_performance=heat_pump_coefficient_of_performance,
                                   chiller_coefficient_of_performance=chiller_coefficient_of_performance,
                                   ambient_temperature_in_degree_celsius=ambient_degree_celsius,
                                   bus_id=bus_id,
                                   simulation_time_series_hour_resolution=simulation_time_series_hour_resolution,
                                   energy_management_system_time_series_resolution_in_hours=
                                   energy_management_system_time_series_resolution_in_hours)

    return [building_asset]


def _create_a_test_energy_system(non_dispatchable_asset: List[NonDispatchableAsset]) -> EnergySystem:
    storage_assets = _create_a_test_storage_asset()
    non_dispatchable_assets = non_dispatchable_asset
    network = _create_a_test_network()
    market = _create_a_test_market()
    simulation_time_series_resolution_in_hours = 0.1
    energy_management_system_time_series_resolution_in_hours = 0.2
    building_assets = _create_a_test_building_asset()
    energy_system = EnergySystem(storage_assets=storage_assets,
                                 non_dispatchable_assets=non_dispatchable_assets,
                                 network=network,
                                 market=market,
                                 simulation_time_series_resolution_in_hours=simulation_time_series_resolution_in_hours,
                                 energy_management_system_time_series_resolution_in_hours=
                                 energy_management_system_time_series_resolution_in_hours,
                                 building_assets=building_assets)

    return energy_system


class TestEnergySystem(unittest.TestCase):

    def test_get_non_dispatchable_assets_active_power_in_kilowatts(self):
        active_power_in_kilowatts = np.array([1, 1, 1])
        reactive_power_in_kilovolt_ampere_reactive = np.array([2, 2, 2])

        non_dispatchable_asset_1 = _create_a_non_dispatchable_test_asset(
            active_power_in_kilowatts=active_power_in_kilowatts,
            reactive_power_in_kilovolt_ampere_reactive=reactive_power_in_kilovolt_ampere_reactive)

        non_dispatchable_asset_2 = _create_a_non_dispatchable_test_asset(
            active_power_in_kilowatts=active_power_in_kilowatts,
            reactive_power_in_kilovolt_ampere_reactive=reactive_power_in_kilovolt_ampere_reactive)

        energy_system = _create_a_test_energy_system(non_dispatchable_asset=
                                                     [non_dispatchable_asset_1, non_dispatchable_asset_2])

        expected_result = np.array([2, 2, 2])
        result = energy_system._get_non_dispatchable_assets_active_power_in_kilowatts()
        np.testing.assert_equal(expected_result, result)

    def test_get_temperature_constraint_for_no_initial_time(self):
        alpha = 0.1
        beta = 0.1
        gamma = 0.1
        previous_building_internal_temperature_in_celsius_degrees = 17.5
        chiller_coefficient_of_performance = 3
        previous_cooling_active_power_in_kilowatts = 500
        heat_pump_coefficient_of_performance = 3.5
        previous_heating_active_power_in_kilowatts = 500
        previous_ambient_temperature_in_degree_celsius = 18

        result = \
            get_temperature_constraint_for_no_initial_time(
                alpha=alpha, beta=beta, gamma=gamma, previous_building_internal_temperature_in_celsius_degrees=
                previous_building_internal_temperature_in_celsius_degrees,
                chiller_coefficient_of_performance=chiller_coefficient_of_performance,
                previous_cooling_active_power_in_kilowatts=previous_cooling_active_power_in_kilowatts,
                heat_pump_coefficient_of_performance=heat_pump_coefficient_of_performance,
                previous_heating_active_power_in_kilowatts=previous_heating_active_power_in_kilowatts,
                previous_ambient_temperature_in_degree_celsius=previous_ambient_temperature_in_degree_celsius)

        expected_result = 28.55
        self.assertEqual(expected_result, result)
