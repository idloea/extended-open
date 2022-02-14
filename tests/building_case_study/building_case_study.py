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
import System.Assets as Assets
import System.Markets as Markets
import System.EnergySystem as EnergySystem
from System.electric_vehicles import ElectricVehicleFleet


### Case Study: Building HVAC flexibility

def get_building_case_original_results(is_winter: bool):
    path_string = normpath('Results/Building_Case_Study/')
    if not os.path.isdir(path_string):
        os.makedirs(path_string)
    ### STEP 0: Load Data

    winter_photovoltaic_electricity_generation_data_path = os.path.join("Data/Building/", "PVpu_1min_2014JAN.csv")
    winter_photovoltaic_electricity_generation_in_per_unit = pd.read_csv(
        winter_photovoltaic_electricity_generation_data_path, index_col=0, parse_dates=True).values

    winter_electric_load_data_path = os.path.join("Data/Building/", "Loads_1min_2014JAN.csv")
    winter_electric_load_data = pd.read_csv(winter_electric_load_data_path, index_col=0, parse_dates=True).values

    summer_photovoltaic_electricity_generation_data_path = os.path.join("Data/Building/", "PVpu_1min_2013JUN.csv")
    summer_photovoltaic_electricity_generation_in_per_unit = pd.read_csv(
        summer_photovoltaic_electricity_generation_data_path, index_col=0, parse_dates=True).values

    summer_electric_load_data_path = os.path.join("Data/Building/", "Loads_1min_2013JUN.csv")
    summer_electric_load_data = pd.read_csv(summer_electric_load_data_path, index_col=0, parse_dates=True).values

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
    time_interval_in_minutes = 1
    time_interval_in_hours = time_interval_in_minutes / 60
    hours_per_day = 24
    number_of_time_intervals_per_day = int(hours_per_day / time_interval_in_hours)

    energy_management_system_time_interval_in_minutes = 15
    energy_management_system_time_interval_in_hours = energy_management_system_time_interval_in_minutes / 60
    number_of_energy_management_system_time_intervals_per_day = int(number_of_time_intervals_per_day *
                                                                    time_interval_in_hours /
                                                                    energy_management_system_time_interval_in_hours)

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
    if not electric_vehicle_fleet.is_electric_vehicle_feasible:
        return

    # Building parameters
    max_inside_degree_celsius = 18
    min_inside_degree_celsius = 16
    initial_inside_degree_celsius = 17  # At the beginning of the scenario
    max_consumed_electric_heating_kilowatts = 90
    max_consumed_electric_cooling_kilowatts = 200
    heat_pump_coefficient_of_performance = 3
    chiller_coefficient_of_performance = 1
    # Parameters from MultiSAVES
    building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = 500  # kWh/ degree celsius
    building_thermal_resistance_in_degree_celsius_per_kilowatts = 0.0337  # degree celsius/kW
    # Market parameters
    # market and EMS have the same time-series
    market_time_interval_in_hours = energy_management_system_time_interval_in_hours
    # market and EMS have same length
    number_of_market_time_intervals_per_day = number_of_energy_management_system_time_intervals_per_day
    # TODO: update prices from https://www.ofgem.gov.uk/publications/feed-tariff-fit-tariff-table-1-april-2021
    prices_export = 0.04  # money received of net exports
    peak_period_import_prices = 0.07
    peak_period_hours_per_day = 7
    valley_period_import_prices = 0.15
    valley_period_hours_per_day = 17

    demand_charge = 0.10  # price per kW for the maximum demand
    max_import_kW = 500  # maximum import power
    min_import_kW = -500  # maximum export power

    offered_kW_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0.6
    min_frequency_response_state_of_charge = 0.4
    frequency_response_price_in_pounds_per_kWh = 5 / 1000
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
    non_dispatchable_photovoltaic_asset = Assets.NonDispatchableAsset(active_power=photovoltaic_active_kilowatts,
                                                                      reactive_power=photovoltaic_reactive_power,
                                                                      bus_id=bus_3,
                                                                      time_intervals_in_hours=time_interval_in_hours,
                                                                      number_of_time_intervals_per_day=
                                                                      number_of_time_intervals_per_day)
    non_distpachable_assets.append(non_dispatchable_photovoltaic_asset)
    # Load at bus 3
    photovoltaic_active_kilowatts = np.sum(electric_loads, 1)  # summed load across 120 households
    photovoltaic_reactive_power = np.zeros(number_of_time_intervals_per_day)
    load_bus3 = Assets.NonDispatchableAsset(photovoltaic_active_kilowatts, photovoltaic_reactive_power,
                                            bus_3,
                                            time_interval_in_hours,
                                            number_of_time_intervals_per_day)
    non_distpachable_assets.append(load_bus3)
    # Building asset at bus 3
    if is_winter:
        ambient_degree_celsius = 10
    else:
        ambient_degree_celsius = 22

    bus_id_building = bus_3
    building = Assets.BuildingAsset(max_inside_degree_celsius=max_inside_degree_celsius,
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
                                    ambient_degree_celsius=ambient_degree_celsius,
                                    bus_id=bus_id_building,
                                    time_intervals_in_hours=time_interval_in_hours,
                                    number_of_time_intervals_per_day=number_of_time_intervals_per_day,
                                    energy_management_system_time_intervals=
                                    energy_management_system_time_interval_in_hours,
                                    number_of_energy_management_system_time_intervals_per_day=
                                    number_of_energy_management_system_time_intervals_per_day)

    building_assets.append(building)

    #######################################
    ### STEP 4: setup the market
    #######################################
    bus_id_market = bus_1
    market = Markets.Market(network_bus_id=bus_id_market,
                            number_of_EMS_time_intervals=number_of_energy_management_system_time_intervals_per_day,
                            export_prices_in_pounds_per_kWh=prices_export,
                            peak_period_import_prices=peak_period_import_prices,
                            peak_period_hours_per_day=peak_period_hours_per_day,
                            valley_period_import_prices=valley_period_import_prices,
                            valley_period_hours_per_day=valley_period_hours_per_day,
                            max_demand_charge_in_pounds_per_kWh=demand_charge,
                            max_import_kW=max_import_kW,
                            min_import_kW=min_import_kW,
                            minutes_market_interval=market_time_interval_in_hours,
                            number_of_market_time_intervals=number_of_market_time_intervals_per_day,
                            offered_kW_in_frequency_response=offered_kW_in_frequency_response,
                            max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                            min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                            frequency_response_price_in_pounds_per_kWh=frequency_response_price_in_pounds_per_kWh,
                            daily_connection_charge=daily_connection_charge)

    #######################################
    # STEP 5: setup the energy system
    #######################################
    energy_system = EnergySystem.EnergySystem(storage_assets=storage_assets,
                                              non_dispatchable_assets=non_distpachable_assets,
                                              network=network,
                                              market=market,
                                              time_intervals_in_hours=time_interval_in_hours,
                                              number_of_time_intervals=number_of_time_intervals_per_day,
                                              energy_management_system_time_intervals_in_hours=
                                              energy_management_system_time_interval_in_hours,
                                              number_of_energy_management_system_time_intervals_per_day=
                                              number_of_energy_management_system_time_intervals_per_day,
                                              building_assets=building_assets)
    #######################################
    ### STEP 6: simulate the energy system:
    #######################################
    output = energy_system.simulate_network()
    # output = energy_system.simulate_network_bldg()
    buses_Vang = output['buses_Vang']
    buses_Pnet = output['buses_Pnet']
    buses_Qnet = output['buses_Qnet']
    Pnet_market = output['Pnet_market']
    Qnet_market = output['Qnet_market']
    buses_Vpu = output['buses_Vpu']
    P_import_ems = output['P_import_ems']
    P_export_ems = output['P_export_ems']
    P_BLDG_ems = output['P_BLDG_ems']
    P_demand_ems = output['P_demand_ems']
    P_demand_base = np.zeros(number_of_time_intervals_per_day)
    for i in range(len(non_distpachable_assets)):
        bus_id = non_distpachable_assets[i].bus_id
        P_demand_base += non_distpachable_assets[i].active_power
    #######################################
    ### STEP 7: plot results
    #######################################
    # x-axis time values
    time = time_interval_in_hours * np.arange(number_of_time_intervals_per_day)
    time_ems = energy_management_system_time_interval_in_hours * np.arange(
        number_of_energy_management_system_time_intervals_per_day)
    timeE = time_interval_in_hours * np.arange(number_of_time_intervals_per_day + 1)
    # Print revenue generated
    revenue = market.calculate_revenue(-Pnet_market, time_interval_in_hours)

    return [revenue,
            buses_Vpu[0],
            buses_Vang[0],
            buses_Pnet[0],
            buses_Qnet[0],
            Pnet_market[0],
            Qnet_market[0],
            P_import_ems[0],
            P_export_ems[0],
            P_BLDG_ems[0],
            P_demand_ems[0],
            P_demand_base[0]]
