import json
import os
from datetime import datetime
from pathlib import Path
from typing import List
import numpy as np
from src import assets, energy_system
from src.buildings import Building
from src.markets import get_market
from src.plot.plots import save_plot_demand_base_and_total_imported_power, save_plot_building_internal_temperature, \
    save_plot_hvac_consumed_active_power_in_kilowatts, save_plot_ambient_temperature, save_plot_import_periods, \
    save_plot_storage_asset_used_power_in_kilowatts
from src.read import read_open_csv_files, read_case_data_from_yaml_file
import pandapower as pp
from src.temperatures import check_initial_inside_degree_celsius
from src.time_intervals import check_sum_of_daily_periods_in_hours_equals_twenty_four, \
    check_unique_hours_of_daily_periods, check_all_hours_of_daily_periods
from src.data_strategy import get_ambient_temperature_in_degree_celsius_by_data_strategy, \
    get_building_electric_loads_by_data_strategy


def run_case(cases_file_path: str, yaml_files: List[str], input_case_data: dict, results_path: Path,
             electric_load_file: str, electric_load_data_file_path: str, building_type: Building) -> None:
    for yaml_file in yaml_files:
        print('YAML FILE:', yaml_file)
        case_data = read_case_data_from_yaml_file(cases_file_path=cases_file_path, file_name=yaml_file)
        market_scenario = case_data['market']

        # STEP 0: Load data
        photovoltaic_generation_data_file = case_data["photovoltaic_generation_data_file_path"]
        photovoltaic_generation_data = read_open_csv_files(csv_file_path=photovoltaic_generation_data_file)
        electric_loads = get_building_electric_loads_by_data_strategy(case_data=case_data,
                                                                      electric_load_data_file_path=
                                                                      electric_load_data_file_path,
                                                                      electric_load_file=electric_load_file)
        hvac_electric_loads = electric_loads * building_type.hvac_percentage_of_electric_load

        # Photovoltaic generation
        sum_of_photovoltaic_generation_in_per_unit = np.sum(photovoltaic_generation_data, 1)
        max_photovoltaic_generation_in_per_unit = np.max(sum_of_photovoltaic_generation_in_per_unit)
        photovoltaic_generation_per_unit = sum_of_photovoltaic_generation_in_per_unit / \
                                           max_photovoltaic_generation_in_per_unit

        rated_photovoltaic_kilowatts = input_case_data["rated_photovoltaic_kilowatts"]

        # STEP 1: setup parameters
        simulation_time_series_resolution_in_minutes = input_case_data["simulation_time_series_resolution_in_minutes"]
        simulation_time_series_resolution_in_hours = simulation_time_series_resolution_in_minutes / 60
        hours_per_day = 24
        number_of_time_intervals_per_day = int(hours_per_day / simulation_time_series_resolution_in_hours)

        energy_management_system_time_series_resolution_in_minutes = \
            input_case_data["energy_management_system_time_series_resolution_in_minutes"]
        energy_management_system_time_series_resolution_in_hours = \
            energy_management_system_time_series_resolution_in_minutes / 60
        number_of_energy_management_time_intervals_per_day = int(hours_per_day /
                                                                 energy_management_system_time_series_resolution_in_hours)

        # Building parameters
        max_inside_degree_celsius = input_case_data["max_inside_degree_celsius"]
        min_inside_degree_celsius = input_case_data["min_inside_degree_celsius"]
        initial_inside_degree_celsius = input_case_data["initial_inside_degree_celsius"]
        check_initial_inside_degree_celsius(initial_inside_degree_celsius=initial_inside_degree_celsius,
                                            max_inside_degree_celsius=max_inside_degree_celsius,
                                            min_inside_degree_celsius=min_inside_degree_celsius)
        max_consumed_electric_heating_kilowatts = input_case_data["max_consumed_electric_heating_kilowatts"]
        max_consumed_electric_cooling_kilowatts = input_case_data["max_consumed_electric_cooling_kilowatts"]
        heat_pump_coefficient_of_performance = input_case_data["heat_pump_coefficient_of_performance"]
        chiller_coefficient_of_performance = input_case_data["chiller_coefficient_of_performance"]

        building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = \
            input_case_data["building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius"]
        building_thermal_resistance_in_degree_celsius_per_kilowatts = \
            input_case_data["building_thermal_resistance_in_degree_celsius_per_kilowatts"]

        market_time_interval_in_hours = energy_management_system_time_series_resolution_in_hours

        export_prices_in_euros_per_kilowatt_hour = input_case_data["export_prices_in_euros_per_kilowatt_hour"]
        import_periods = case_data["import_periods"]
        import_period_prices = None
        if market_scenario == 'Spanish':
            check_sum_of_daily_periods_in_hours_equals_twenty_four(periods=import_periods)
            check_unique_hours_of_daily_periods(periods=import_periods)
            check_all_hours_of_daily_periods(periods=import_periods)
            import_period_prices = input_case_data["import_period_prices"]
        demand_charge_in_euros_per_kilowatt = input_case_data["demand_charge_in_euros_per_kilowatt"]
        max_import_kilowatts = input_case_data["max_import_kilowatts"]
        max_export_kilowatts = input_case_data["max_export_kilowatts"]
        offered_kilowatts_in_frequency_response = input_case_data["offered_kilowatts_in_frequency_response"]
        max_frequency_response_state_of_charge = input_case_data["max_frequency_response_state_of_charge"]
        min_frequency_response_state_of_charge = input_case_data["min_frequency_response_state_of_charge"]
        frequency_response_price_in_euros_per_kilowatt_hour = input_case_data[
            "frequency_response_price_in_euros_per_kilowatt_hour"]

        # STEP 2: set up the network
        network = pp.create_empty_network()

        grid_1_voltage_level_in_kilo_volts: int = input_case_data["grid_1_voltage_level_in_kilo_volts"]
        grid_2_voltage_level_in_kilo_volts: float = input_case_data["grid_2_voltage_level_in_kilo_volts"]
        grid_3_voltage_level_in_kilo_volts: float = input_case_data["grid_3_voltage_level_in_kilo_volts"]

        bus_1 = pp.create_bus(network, vn_kv=grid_1_voltage_level_in_kilo_volts, name="bus 1")
        bus_2 = pp.create_bus(network, vn_kv=grid_2_voltage_level_in_kilo_volts, name="bus 2")
        bus_3 = pp.create_bus(network, vn_kv=grid_3_voltage_level_in_kilo_volts, name="bus 3")

        pp.create_ext_grid(network, bus=bus_1, vm_pu=1.0, name="Grid Connection")

        high_voltage_bus = bus_1
        low_voltage_bus = bus_2

        transformer_apparent_power_in_mega_volt_ampere = input_case_data[
            "transformer_apparent_power_in_mega_volt_ampere"]
        trafo_std_type = f"{transformer_apparent_power_in_mega_volt_ampere} MVA {grid_1_voltage_level_in_kilo_volts}" \
                         f"/{grid_2_voltage_level_in_kilo_volts} kV"
        trafo = pp.create_transformer(network, hv_bus=high_voltage_bus, lv_bus=low_voltage_bus, std_type=trafo_std_type,
                                      name="Trafo")

        length_from_bus_2_to_bus_3_in_km = input_case_data["length_from_bus_2_to_bus_3_in_km"]
        line = pp.create_line(network, from_bus=bus_2, to_bus=bus_3, length_km=length_from_bus_2_to_bus_3_in_km,
                              std_type="NAYY 4x50 SE", name="Line")

        # STEP 3: setup the assets
        storage_assets = []
        building_assets = []
        non_distpachable_assets = []

        max_storage_asset_energy_in_kilowatt_hour = \
            np.full((number_of_time_intervals_per_day,), input_case_data['max_storage_asset_energy_in_kilowatt_hour'])
        min_storage_asset_energy_in_kilowatt_hour = \
            np.full((number_of_time_intervals_per_day,), input_case_data['min_storage_asset_energy_in_kilowatt_hour'])
        max_storage_asset_active_power_in_kilowatts = \
            np.full((number_of_time_intervals_per_day,), input_case_data['max_storage_asset_active_power_in_kilowatts'])
        min_storage_asset_active_power_in_kilowatts = \
            np.full((number_of_time_intervals_per_day,), input_case_data['min_storage_asset_active_power_in_kilowatts'])
        initial_storage_asset_energy_level_in_kilowatt_hour = \
            input_case_data['initial_storage_asset_energy_level_percentage'] / 100 * input_case_data[
                'max_storage_asset_energy_in_kilowatt_hour']
        required_storage_asset_terminal_energy_level_in_kilowatt_hour = \
            input_case_data['required_storage_asset_terminal_energy_level_percentage'] / 100 * \
            input_case_data['max_storage_asset_energy_in_kilowatt_hour']
        storage_asset_absolute_active_power_in_kilowatts = \
            input_case_data['storage_asset_absolute_active_power_in_kilowatts']
        storage_asset_battery_degradation_ratio_in_euros_per_kilowatt_hour = \
            input_case_data['storage_asset_degradation_ratio_in_euros_per_kilowatt_hour']
        storage_asset_charging_efficiency = input_case_data['storage_asset_charging_efficiency_percentage'] / 100
        storage_asset_charging_efficiency_for_the_optimizer = \
            input_case_data['storage_asset_charging_efficiency_for_the_optimizer_percentage'] / 100
        storage_assets_bus_id = bus_3
        storage_assets_battery_system = assets.StorageAsset(
            max_energy_in_kilowatt_hour=max_storage_asset_energy_in_kilowatt_hour,
            min_energy_in_kilowatt_hour=min_storage_asset_energy_in_kilowatt_hour,
            max_active_power_in_kilowatts=max_storage_asset_active_power_in_kilowatts,
            min_active_power_in_kilowatts=min_storage_asset_active_power_in_kilowatts,
            initial_energy_level_in_kilowatt_hour=initial_storage_asset_energy_level_in_kilowatt_hour,
            required_terminal_energy_level_in_kilowatt_hour=
            required_storage_asset_terminal_energy_level_in_kilowatt_hour,
            bus_id=storage_assets_bus_id,
            simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours,
            number_of_time_intervals_per_day=number_of_time_intervals_per_day,
            energy_management_system_time_series_resolution_in_seconds=
            energy_management_system_time_series_resolution_in_hours,
            number_of_energy_management_system_time_intervals_per_day=
            number_of_energy_management_time_intervals_per_day,
            absolute_active_power_in_kilowatts=storage_asset_absolute_active_power_in_kilowatts,
            battery_degradation_ratio_in_euros_per_kilowatt_hour=
            storage_asset_battery_degradation_ratio_in_euros_per_kilowatt_hour,
            charging_efficiency=storage_asset_charging_efficiency,
            charging_efficiency_for_the_optimizer=storage_asset_charging_efficiency_for_the_optimizer)
        storage_assets.append(storage_assets_battery_system)

        photovoltaic_active_power_in_kilowatts = -photovoltaic_generation_per_unit * rated_photovoltaic_kilowatts  # Negative as it generates energy
        photovoltaic_reactive_power_in_kilovolt_ampere = np.zeros(number_of_time_intervals_per_day)
        non_dispatchable_photovoltaic_asset = assets.NonDispatchableAsset(
            simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
            active_power_in_kilowatts=photovoltaic_active_power_in_kilowatts,
            reactive_power_in_kilovolt_ampere_reactive=photovoltaic_reactive_power_in_kilovolt_ampere)
        non_distpachable_assets.append(non_dispatchable_photovoltaic_asset)

        electric_load_active_power_in_kilowatts = np.array(hvac_electric_loads)
        electric_load_reactive_power_in_kilovolt_ampere_reactive = np.zeros(number_of_time_intervals_per_day)
        non_dispatchable_electric_load_at_bus_3 = assets.NonDispatchableAsset(
            simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
            active_power_in_kilowatts=electric_load_active_power_in_kilowatts,
            reactive_power_in_kilovolt_ampere_reactive=electric_load_reactive_power_in_kilovolt_ampere_reactive)
        non_distpachable_assets.append(non_dispatchable_electric_load_at_bus_3)

        ambient_temperature_in_degree_celsius = get_ambient_temperature_in_degree_celsius_by_data_strategy(
            case_data=case_data,
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day)

        # Building asset at bus 3
        bus_id_building = bus_3
        building = assets.BuildingAsset(max_inside_degree_celsius=max_inside_degree_celsius,
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
                                        ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius,
                                        bus_id=bus_id_building,
                                        simulation_time_series_hour_resolution=
                                        simulation_time_series_resolution_in_hours,
                                        energy_management_system_time_series_resolution_in_hours=
                                        energy_management_system_time_series_resolution_in_hours)

        building_assets.append(building)

        # STEP 4: setup the market
        bus_id_market = bus_1
        market = get_market(case_data=case_data,
                            import_period_prices=import_period_prices,
                            network_bus_id=bus_id_market,
                            market_time_series_resolution_in_hours=market_time_interval_in_hours,
                            export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                            import_periods=import_periods,
                            max_demand_charge_in_euros_per_kilowatt_hour=demand_charge_in_euros_per_kilowatt,
                            max_import_kilowatts=max_import_kilowatts,
                            max_export_kilowatts=max_export_kilowatts,
                            offered_kilowatt_in_frequency_response=offered_kilowatts_in_frequency_response,
                            max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                            min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                            frequency_response_price_in_euros_per_kilowatt_hour=
                            frequency_response_price_in_euros_per_kilowatt_hour)

        # STEP 5: setup the energy system
        case_energy_system = energy_system.EnergySystem(storage_assets=storage_assets,
                                                        non_dispatchable_assets=non_distpachable_assets,
                                                        network=network,
                                                        market=market,
                                                        simulation_time_series_resolution_in_hours=
                                                        simulation_time_series_resolution_in_hours,
                                                        energy_management_system_time_series_resolution_in_hours=
                                                        energy_management_system_time_series_resolution_in_hours,
                                                        building_assets=building_assets,
                                                        blackout_start_time_in_hours=
                                                        input_case_data['blackout_start_time_in_hours'],
                                                        blackout_stop_time_in_hours=
                                                        input_case_data['blackout_stop_time_in_hours']
                                                        )

        # STEP 6: simulate the energy system:
        output = case_energy_system.simulate_network()
        buses_voltage_angle_in_degrees = output['buses_voltage_angle_in_degrees']
        buses_active_power_in_kilowatts = output['buses_active_power_in_kilowatts']
        buses_reactive_power_in_kilovolt_ampere_reactive = output['buses_reactive_power_in_kilovolt_ampere_reactive']
        market_active_power_in_kilowatts = output['market_active_power_in_kilowatts']
        market_reactive_power_in_kilovolt_ampere_reactive = output['market_reactive_power_in_kilovolt_ampere_reactive']
        buses_voltage_in_per_unit = output['buses_voltage_in_per_unit']
        imported_active_power_in_kilowatts = \
            output['imported_active_power_in_kilowatts']
        exported_active_power_in_kilowatts = \
            output['exported_active_power_in_kilowatts']
        building_power_consumption_in_kilowatts = \
            output['building_power_consumption_in_kilowatts']
        active_power_demand_in_kilowatts = \
            output['active_power_demand_in_kilowatts']
        active_power_demand_base_in_kilowatts = np.zeros(number_of_time_intervals_per_day)
        storage_asset_accumulated_power_in_kilowatts = \
            output['storage_asset_accumulated_power_in_kilowatts']

        for non_dispatchable_asset in range(len(non_distpachable_assets)):
            bus_id = non_distpachable_assets[non_dispatchable_asset].bus_id
            active_power_demand_base_in_kilowatts += non_distpachable_assets[
                non_dispatchable_asset].active_power_in_kilowatts

        revenue = \
            round(
                market.calculate_revenue(-market_active_power_in_kilowatts, simulation_time_series_resolution_in_hours),
                2)
        print('Revenue in euros:', revenue)

        current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        case_file_name = electric_load_file.split('.')[0]
        month = case_data['month']
        plots_path = f'{results_path}/{current_time}_{month}_{case_file_name}'
        os.mkdir(path=plots_path)
        save_plot_demand_base_and_total_imported_power(
            simulation_time_series_resolution_in_hours=simulation_time_series_resolution_in_hours,
            number_of_time_intervals_per_day=number_of_time_intervals_per_day,
            active_power_demand_base_in_kilowatts=active_power_demand_base_in_kilowatts,
            market_active_power_in_kilowatts=market_active_power_in_kilowatts, case=electric_load_file, revenue=revenue,
            current_time=current_time, plots_path=plots_path)

        save_plot_ambient_temperature(
            energy_management_system_time_series_resolution_in_hours=
            energy_management_system_time_series_resolution_in_hours,
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day,
            ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius, case=electric_load_file,
            current_time=current_time, plots_path=plots_path)

        number_of_buildings = len(building_assets)
        save_plot_building_internal_temperature(number_of_buildings=number_of_buildings,
                                                energy_management_system_time_series_resolution_in_hours=
                                                energy_management_system_time_series_resolution_in_hours,
                                                number_of_energy_management_time_intervals_per_day=
                                                number_of_energy_management_time_intervals_per_day,
                                                building_assets=building_assets, case=electric_load_file,
                                                current_time=current_time,
                                                plots_path=plots_path)

        save_plot_hvac_consumed_active_power_in_kilowatts(number_of_buildings=number_of_buildings,
                                                          simulation_time_series_resolution_in_hours=
                                                          simulation_time_series_resolution_in_hours,
                                                          number_of_time_intervals_per_day=
                                                          number_of_time_intervals_per_day,
                                                          energy_management_system_time_series_resolution_in_hours=
                                                          energy_management_system_time_series_resolution_in_hours,
                                                          number_of_energy_management_time_intervals_per_day=
                                                          number_of_energy_management_time_intervals_per_day,
                                                          building_assets=building_assets,
                                                          max_consumed_electric_heating_kilowatts=None,
                                                          max_consumed_electric_cooling_kilowatts=
                                                          max_consumed_electric_cooling_kilowatts,
                                                          case=electric_load_file,
                                                          current_time=current_time, plots_path=plots_path)

        save_plot_import_periods(energy_management_system_time_series_resolution_in_hours=
                                 energy_management_system_time_series_resolution_in_hours,
                                 number_of_energy_management_time_intervals_per_day=
                                 number_of_energy_management_time_intervals_per_day,
                                 import_periods=import_periods, case=electric_load_file, current_time=current_time,
                                 plots_path=plots_path)

        save_plot_storage_asset_used_power_in_kilowatts(energy_management_system_time_series_resolution_in_hours=
                                                        energy_management_system_time_series_resolution_in_hours,
                                                        number_of_energy_management_time_intervals_per_day=
                                                        number_of_energy_management_time_intervals_per_day,
                                                        storage_asset_accumulated_power_in_kilowatts=
                                                        storage_asset_accumulated_power_in_kilowatts,
                                                        case=electric_load_file, current_time=current_time,
                                                        plots_path=plots_path)

        input_case_data['photovoltaic_generation_data_file_path'] = case_data[
            'photovoltaic_generation_data_file_path']
        input_case_data['electric_load_data_file_path'] = electric_load_data_file_path
        input_case_data['data_strategy'] = case_data['data_strategy']
        input_case_data['ambient_temperature_file_path'] = case_data['ambient_temperature_file_path']
        input_case_data['market'] = case_data['market']

        with open(f"{plots_path}/input_case_data.json", "w") as outfile:
            json.dump(input_case_data, outfile, indent=4)

        output_case_data = {
            'buses_voltage_angle_in_degrees': buses_voltage_angle_in_degrees.tolist(),
            'buses_active_power_in_kilowatts': buses_active_power_in_kilowatts.tolist(),
            'buses_reactive_power_in_kilovolt_ampere_reactive': buses_reactive_power_in_kilovolt_ampere_reactive.tolist(),
            'market_active_power_in_kilowatts': market_active_power_in_kilowatts.tolist(),
            'market_reactive_power_in_kilovolt_ampere_reactive': market_reactive_power_in_kilovolt_ampere_reactive.tolist(),
            'buses_voltage_in_per_unit': buses_voltage_in_per_unit.tolist(),
            'active_power_demand_in_kilowatts': active_power_demand_in_kilowatts.tolist(),
            'revenue': revenue,
            'active_power_demand_base_in_kilowatts': active_power_demand_base_in_kilowatts.tolist()
        }

        with open(f"{plots_path}/output_case_data.json", "w") as outfile:
            json.dump(output_case_data, outfile, indent=4)
