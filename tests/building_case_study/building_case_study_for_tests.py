# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The building energy management case study focuses on a building with a flexible
HVAC unit which is controlled in order to minimise costs, with the constraint
that the internal temperature remains between 16 and 18 degrees C.
"""

import os
from os.path import normpath
import pandas as pd
import pandapower as pp
import numpy as np
import src.assets as Assets
import src.markets as Markets
import src.energy_system as EnergySystem
from src.electric_vehicles import ElectricVehicleFleet
from src.folder_management import create_results_folder
from src.read import read_open_csv_files


### Case Study: Building HVAC flexibility

def get_building_case_original_results(is_winter: bool):
    results_path = 'Results/Building_Case_Study/'
    create_results_folder(results_path=results_path)
    ### STEP 0: Load data

    building_data_path = "data/Building/"

    winter_photovoltaic_data_file = "PVpu_1min_2014JAN.csv"
    winter_photovoltaic_electricity_generation_in_per_unit = read_open_csv_files(path=building_data_path,
                                                                                 csv_file=winter_photovoltaic_data_file)
    winter_electric_load_data_file = "Loads_1min_2014JAN.csv"
    winter_electric_load_data = read_open_csv_files(path=building_data_path, csv_file=winter_electric_load_data_file)

    summer_photovoltaic_data_file = "PVpu_1min_2013JUN.csv"
    summer_photovoltaic_electricity_generation_in_per_unit = read_open_csv_files(path=building_data_path,
                                                                                 csv_file=summer_photovoltaic_data_file)
    summer_electric_load_data_file = "Loads_1min_2013JUN.csv"
    summer_electric_load_data = read_open_csv_files(path=building_data_path, csv_file=summer_electric_load_data_file)

    sum_of_summer_photovoltaic_electricity_generation_in_per_unit = np.sum(
        summer_photovoltaic_electricity_generation_in_per_unit, 1)
    sum_of_winter_photovoltaic_electricity_generation_in_per_unit = np.sum(
        winter_photovoltaic_electricity_generation_in_per_unit, 1)

    if not is_winter:
        photovoltaic_generation_per_unit = sum_of_summer_photovoltaic_electricity_generation_in_per_unit / \
                                           np.max(sum_of_summer_photovoltaic_electricity_generation_in_per_unit)
        electric_loads = summer_electric_load_data
    else:
        photovoltaic_generation_per_unit = sum_of_winter_photovoltaic_electricity_generation_in_per_unit / \
                                           np.max(sum_of_summer_photovoltaic_electricity_generation_in_per_unit)
        electric_loads = winter_electric_load_data

    ### STEP 1: setup parameters
    simulation_time_series_resolution_in_minutes = 1
    simulation_time_series_resolution_in_hours = simulation_time_series_resolution_in_minutes / 60
    hours_per_day = 24
    number_of_time_intervals_per_day = int(hours_per_day / simulation_time_series_resolution_in_hours)

    energy_management_system_time_series_minute_resolution = 15
    energy_management_system_time_series_hour_resolution = energy_management_system_time_series_minute_resolution / 60
    number_of_energy_management_system_time_intervals_per_day = int(
        hours_per_day / energy_management_system_time_series_hour_resolution)

    rated_photovoltaic_kilowatts = 400

    # Electric Vehicle (EV) parameters
    seed = 1000  # Used by OPEN originally
    random_seed = np.random.seed(seed)
    number_of_electric_vehicles = 120
    max_battery_capacity_in_kilowatts_per_hour = 30
    max_battery_charging_power_in_kilowatts = 7
    electric_vehicle_arrival_time_start = 12
    electric_vehicle_arrival_time_end = 22
    electric_vehicle_departure_time_start = 5
    electric_vehicle_departure_time_end = 8

    electric_vehicle_fleet = ElectricVehicleFleet(random_seed=random_seed,
                                                  number_of_electric_vehicles=number_of_electric_vehicles,
                                                  max_battery_capacity_in_kilowatts_per_hour=
                                                  max_battery_capacity_in_kilowatts_per_hour,
                                                  max_electric_vehicle_charging_power=
                                                  max_battery_charging_power_in_kilowatts,
                                                  electric_vehicle_arrival_time_start=
                                                  electric_vehicle_arrival_time_start,
                                                  electric_vehicle_arrival_time_end=electric_vehicle_arrival_time_end,
                                                  electric_vehicle_departure_time_start=
                                                  electric_vehicle_departure_time_start,
                                                  electric_vehicle_departure_time_end=
                                                  electric_vehicle_departure_time_end
                                                  )

    electric_vehicle_fleet.check_electric_vehicle_fleet_charging_feasibility()
    if not electric_vehicle_fleet.is_electric_vehicle_fleet_feasible_for_the_system:
        return

    # Building parameters
    max_allowed_building_degree_celsius = 18
    min_allowed_building_degree_celsius = 16
    initial_building_degree_celsius = 17  # At the beginning of the scenario
    max_consumed_electric_heating_kilowatts = 90
    max_consumed_electric_cooling_kilowatts = 200
    heat_pump_coefficient_of_performance = 3
    chiller_coefficient_of_performance = 1
    # Parameters from MultiSAVES
    building_thermal_mass_in_kilowatts_hour_per_degree_celsius = 500  # kWh/ degree celsius
    building_heat_transfer_in_degree_celsius_per_kilowatts = 0.0337  # degree celsius/kW
    # Market parameters
    # market and EMS have the same time-series
    market_time_interval_in_hours = energy_management_system_time_series_hour_resolution
    # market and EMS have same length
    # TODO: update prices from https://www.ofgem.gov.uk/publications/feed-tariff-fit-tariff-table-1-april-2021
    prices_export_in_euros_per_kilowatt_hour = 0.04  # money received of net exports

    period_one_name = 'peak'
    period_one_hours = 7
    period_one_euros_per_kilowatt_hour = 0.07
    period_two_name = 'valley'
    period_two_hours = 17
    period_two_euros_per_kilowatt_hour = 0.15

    import_periods = [{period_one_name: [period_one_hours, period_one_euros_per_kilowatt_hour]},
                      {period_two_name: [period_two_hours, period_two_euros_per_kilowatt_hour]}]

    demand_charge_in_euros_per_kilowatt = 0.10  # for the maximum power import over the day
    max_import_kilowatts = 500  # maximum import power
    max_export_kilowatts = -500  # maximum export power

    offered_kilowatts_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0.6
    min_frequency_response_state_of_charge = 0.4
    frequency_response_price_in_euros_per_kilowatt_hour = 0.005
    #######################################
    ### STEP 2: setup the network
    #######################################
    # (from https://github.com/e2nIEE/pandapower/blob/master/tutorials/minimal_example.ipynb)
    network = pp.create_empty_network()
    # create buses
    bus_1 = pp.create_bus(network, vn_kv=20., name="bus 1")
    bus_2 = pp.create_bus(network, vn_kv=0.4, name="bus 2")
    bus_3 = pp.create_bus(network, vn_kv=0.4, name="bus 3")
    # create bus elements
    pp.create_ext_grid(network, bus=bus_1, vm_pu=1.0, name="Grid Connection")
    # create branch elements
    trafo = pp.create_transformer(network, hv_bus=bus_1, lv_bus=bus_2, std_type="0.4 MVA 20/0.4 kV", name="Trafo")
    line = pp.create_line(network, from_bus=bus_2, to_bus=bus_3, length_km=0.1, std_type="NAYY 4x50 SE", name="Line")
    number_of_buses = network.bus['name'].size
    #######################################
    ### STEP 3: setup the assets
    #######################################
    # initiate empty lists for different types of assets
    storage_assets = []
    building_assets = []
    non_distpachable_assets = []
    # PV source at bus 3
    photovoltaic_active_power_in_kilowatts = -photovoltaic_generation_per_unit * rated_photovoltaic_kilowatts  # Negative as it generates energy
    photovoltaic_reactive_power_in_kilovolt_ampere_reactive = np.zeros(
        number_of_time_intervals_per_day)  # Solar panels won't produce reactive power being a DC generator
    non_dispatchable_photovoltaic_asset = Assets.NonDispatchableAsset(
        simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
        active_power_in_kilowatts=photovoltaic_active_power_in_kilowatts,
        reactive_power_in_kilovolt_ampere_reactive=photovoltaic_reactive_power_in_kilovolt_ampere_reactive)
    non_distpachable_assets.append(non_dispatchable_photovoltaic_asset)
    # Load at bus 3
    electric_load_active_power_in_kilowatts = np.sum(electric_loads, 1)  # summed load across 120 households
    electric_load_reactive_power_in_kilovolt_ampere_reactive = np.zeros(number_of_time_intervals_per_day)
    non_dispatchable_electric_load_at_bus_3 = Assets.NonDispatchableAsset(
        simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
        active_power_in_kilowatts=electric_load_active_power_in_kilowatts,
        reactive_power_in_kilovolt_ampere_reactive=electric_load_reactive_power_in_kilovolt_ampere_reactive)

    non_distpachable_assets.append(non_dispatchable_electric_load_at_bus_3)
    # Building asset at bus 3
    if is_winter:
        ambient_temperature_in_degree_celsius = 10
    else:
        ambient_temperature_in_degree_celsius = 22

    bus_id_building = bus_3
    building = Assets.BuildingAsset(max_inside_degree_celsius=max_allowed_building_degree_celsius,
                                    min_inside_degree_celsius=min_allowed_building_degree_celsius,
                                    max_consumed_electric_heating_kilowatts=max_consumed_electric_heating_kilowatts,
                                    max_consumed_electric_cooling_kilowatts=max_consumed_electric_cooling_kilowatts,
                                    initial_inside_degree_celsius=initial_building_degree_celsius,
                                    building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius=
                                    building_thermal_mass_in_kilowatts_hour_per_degree_celsius,
                                    building_thermal_resistance_in_degree_celsius_per_kilowatts=
                                    building_heat_transfer_in_degree_celsius_per_kilowatts,
                                    heat_pump_coefficient_of_performance=heat_pump_coefficient_of_performance,
                                    chiller_coefficient_of_performance=chiller_coefficient_of_performance,
                                    ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius,
                                    bus_id=bus_id_building,
                                    simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours,
                                    energy_management_system_time_series_resolution_in_hours=
                                    energy_management_system_time_series_hour_resolution)

    building_assets.append(building)

    #######################################
    ### STEP 4: setup the market
    #######################################
    bus_id_market = bus_1
    market = Markets.OPENMarket(network_bus_id=bus_id_market,
                                market_time_series_resolution_in_hours=market_time_interval_in_hours,
                                export_prices_in_euros_per_kilowatt_hour=prices_export_in_euros_per_kilowatt_hour,
                                import_periods=import_periods,
                                max_demand_charge_in_euros_per_kilowatt_hour=demand_charge_in_euros_per_kilowatt,
                                max_import_kilowatts=max_import_kilowatts, max_export_kilowatts=max_export_kilowatts,
                                offered_kilowatt_in_frequency_response=offered_kilowatts_in_frequency_response,
                                max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                                min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                                frequency_response_price_in_euros_per_kilowatt_hour=frequency_response_price_in_euros_per_kilowatt_hour)

    #######################################
    # STEP 5: setup the energy system
    #######################################
    energy_system = EnergySystem.EnergySystem(storage_assets=storage_assets,
                                              non_dispatchable_assets=non_distpachable_assets,
                                              network=network,
                                              market=market,
                                              simulation_time_series_resolution_in_hours=
                                              simulation_time_series_resolution_in_hours,
                                              energy_management_system_time_series_resolution_in_hours=
                                              energy_management_system_time_series_hour_resolution,
                                              building_assets=building_assets)
    #######################################
    ### STEP 6: simulate the energy system:
    #######################################
    output = energy_system.simulate_network()
    buses_voltage_angle_in_degrees = output['buses_voltage_angle_in_degrees']
    buses_active_power_in_kilowatts = output['buses_active_power_in_kilowatts']
    buses_reactive_power_in_kilovolt_ampere_reactive = output['buses_reactive_power_in_kilovolt_ampere_reactive']
    market_active_power_in_kilowatts = output['market_active_power_in_kilowatts']
    market_reactive_power_in_kilovolt_ampere_reactive = output['market_reactive_power_in_kilovolt_ampere_reactive']
    buses_voltage_in_per_unit = output['buses_voltage_in_per_unit']
    imported_active_power_in_kilowatts = output['imported_active_power_in_kilowatts']
    exported_active_power_in_kilowatts = output['exported_active_power_in_kilowatts']
    building_power_consumption_in_kilowatts = \
        output['building_power_consumption_in_kilowatts']
    active_power_demand_in_kilowatts = output['active_power_demand_in_kilowatts']
    active_power_demand_base_in_kilowatts = np.zeros(number_of_time_intervals_per_day)
    for i in range(len(non_distpachable_assets)):
        bus_id = non_distpachable_assets[i].bus_id
        active_power_demand_base_in_kilowatts += non_distpachable_assets[i].active_power_in_kilowatts
    #######################################
    ### STEP 7: plot results
    #######################################
    # x-axis time values
    time = simulation_time_series_resolution_in_hours * np.arange(number_of_time_intervals_per_day)
    time_ems = energy_management_system_time_series_hour_resolution * np.arange(
        number_of_energy_management_system_time_intervals_per_day)
    timeE = simulation_time_series_resolution_in_hours * np.arange(number_of_time_intervals_per_day + 1)
    # Print revenue generated
    revenue = market.calculate_revenue(-market_active_power_in_kilowatts, simulation_time_series_resolution_in_hours)

    return [revenue,
            buses_voltage_in_per_unit[0],
            buses_voltage_angle_in_degrees[0],
            buses_active_power_in_kilowatts[0],
            buses_reactive_power_in_kilovolt_ampere_reactive[0],
            market_active_power_in_kilowatts[0],
            market_reactive_power_in_kilovolt_ampere_reactive[0],
            imported_active_power_in_kilowatts[0],
            exported_active_power_in_kilowatts[0],
            building_power_consumption_in_kilowatts[0],
            active_power_demand_in_kilowatts[0],
            active_power_demand_base_in_kilowatts[0]]
