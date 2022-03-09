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
import src.Assets as Assets
import src.Markets as Markets
import src.EnergySystem as EnergySystem
from src.electric_vehicles import ElectricVehicleFleet
from src.folder_management import create_results_folder
from src.read import read_open_csv_files


### Case Study: Building HVAC flexibility

def get_building_case_original_results(is_winter: bool):
    results_path = 'Results/Building_Case_Study/'
    create_results_folder(results_path=results_path)
    ### STEP 0: Load Data

    building_data_path = "Data/Building/"

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
    simulation_time_series_minute_resolution = 1
    simulation_time_series_hour_resolution = simulation_time_series_minute_resolution / 60
    hours_per_day = 24
    number_of_time_intervals_per_day = int(hours_per_day / simulation_time_series_hour_resolution)

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
    prices_export_in_pounds_per_kilowatt_hour = 0.04  # money received of net exports
    peak_period_import_prices_in_pounds_per_kilowatt_hour = 0.07
    peak_period_hours_per_day = 7
    valley_period_import_prices_in_pounds_per_kilowatt_hour = 0.15
    valley_period_hours_per_day = 17

    demand_charge_in_pounds_per_kilowatt = 0.10  # for the maximum power import over the day
    max_import_kilowatts = 500  # maximum import power
    max_export_kilowatts = -500  # maximum export power

    offered_kilowatts_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0.6
    min_frequency_response_state_of_charge = 0.4
    frequency_response_price_in_pounds_per_kilowatt_hour = 0.005
    daily_connection_charge = 0.13
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
    photovoltaic_active_kilowatts = -photovoltaic_generation_per_unit * rated_photovoltaic_kilowatts  # Negative as it generates energy
    photovoltaic_reactive_power = np.zeros(
        number_of_time_intervals_per_day)  # Solar panels won't produce reactive power being a DC generator
    non_dispatchable_photovoltaic_asset = Assets.NonDispatchableAsset(
        simulation_time_series_hour_resolution=simulation_time_series_hour_resolution, bus_id=bus_3,
        active_power=photovoltaic_active_kilowatts, reactive_power=photovoltaic_reactive_power)
    non_distpachable_assets.append(non_dispatchable_photovoltaic_asset)
    # Load at bus 3
    photovoltaic_active_kilowatts = np.sum(electric_loads, 1)  # summed load across 120 households
    photovoltaic_reactive_power = np.zeros(number_of_time_intervals_per_day)
    load_bus3 = Assets.NonDispatchableAsset(simulation_time_series_hour_resolution=
                                            simulation_time_series_hour_resolution,
                                            bus_id=bus_3,
                                            active_power=photovoltaic_active_kilowatts,
                                            reactive_power=photovoltaic_reactive_power
                                            )

    non_distpachable_assets.append(load_bus3)
    # Building asset at bus 3
    if is_winter:
        ambient_degree_celsius = 10
    else:
        ambient_degree_celsius = 22

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
                                    ambient_degree_celsius=ambient_degree_celsius,
                                    bus_id=bus_id_building,
                                    simulation_time_series_hour_resolution=simulation_time_series_hour_resolution,
                                    energy_management_system_time_series_hour_resolution=
                                    energy_management_system_time_series_hour_resolution)

    building_assets.append(building)

    #######################################
    ### STEP 4: setup the market
    #######################################
    bus_id_market = bus_1
    market = Markets.Market(network_bus_id=bus_id_market,
                            market_time_series_minute_resolution=market_time_interval_in_hours,
                            export_prices_in_pounds_per_kilowatt_hour=prices_export_in_pounds_per_kilowatt_hour,
                            peak_period_import_prices_in_pounds_per_kilowatt_hour=peak_period_import_prices_in_pounds_per_kilowatt_hour,
                            peak_period_hours_per_day=peak_period_hours_per_day,
                            valley_period_import_prices_in_pounds_per_kilowatt_hour=valley_period_import_prices_in_pounds_per_kilowatt_hour,
                            valley_period_hours_per_day=valley_period_hours_per_day,
                            max_demand_charge_in_pounds_per_kWh=demand_charge_in_pounds_per_kilowatt,
                            max_import_kilowatts=max_import_kilowatts,
                            max_export_kilowatts=max_export_kilowatts,
                            offered_kW_in_frequency_response=offered_kilowatts_in_frequency_response,
                            max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                            min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                            frequency_response_price_in_pounds_per_kilowatt_hour=
                            frequency_response_price_in_pounds_per_kilowatt_hour,
                            daily_connection_charge=daily_connection_charge)

    #######################################
    # STEP 5: setup the energy system
    #######################################
    energy_system = EnergySystem.EnergySystem(storage_assets=storage_assets,
                                              non_dispatchable_assets=non_distpachable_assets,
                                              network=network,
                                              market=market,
                                              simulation_time_series_resolution_in_hours=
                                              simulation_time_series_hour_resolution,
                                              energy_management_system_time_series_resolution_in_hours=
                                              energy_management_system_time_series_hour_resolution,
                                              building_assets=building_assets)
    #######################################
    ### STEP 6: simulate the energy system:
    #######################################
    output = energy_system.simulate_network()
    buses_voltage_angle_in_degrees = output['buses_Vang']
    buses_active_power_in_kilowatts = output['buses_Pnet']
    buses_reactive_power = output['buses_Qnet']
    market_active_power_in_kilowatts = output['Pnet_market']
    market_reactive_power = output['Qnet_market']
    buses_voltage_in_per_unit = output['buses_Vpu']
    energy_management_system_imported_active_power_in_kilowatts = output['P_import_ems']
    energy_management_system_exported_active_power_in_kilowatts = output['P_export_ems']
    building_energy_management_system_active_power_in_kilowatts = output['P_BLDG_ems']
    energy_management_system_active_power_demand_in_kilowatt = output['P_demand_ems']
    active_power_demand_base_in_kilowatts = np.zeros(number_of_time_intervals_per_day)
    for i in range(len(non_distpachable_assets)):
        bus_id = non_distpachable_assets[i].bus_id
        active_power_demand_base_in_kilowatts += non_distpachable_assets[i].active_power
    #######################################
    ### STEP 7: plot results
    #######################################
    # x-axis time values
    time = simulation_time_series_hour_resolution * np.arange(number_of_time_intervals_per_day)
    time_ems = energy_management_system_time_series_hour_resolution * np.arange(
        number_of_energy_management_system_time_intervals_per_day)
    timeE = simulation_time_series_hour_resolution * np.arange(number_of_time_intervals_per_day + 1)
    # Print revenue generated
    revenue = market.calculate_revenue(-market_active_power_in_kilowatts, simulation_time_series_hour_resolution)

    return [revenue,
            buses_voltage_in_per_unit[0],
            buses_voltage_angle_in_degrees[0],
            buses_active_power_in_kilowatts[0],
            buses_reactive_power[0],
            market_active_power_in_kilowatts[0],
            market_reactive_power[0],
            energy_management_system_imported_active_power_in_kilowatts[0],
            energy_management_system_exported_active_power_in_kilowatts[0],
            building_energy_management_system_active_power_in_kilowatts[0],
            energy_management_system_active_power_demand_in_kilowatt[0],
            active_power_demand_base_in_kilowatts[0]]
