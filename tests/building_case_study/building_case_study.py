
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The building energy management case study focuses on a building with a flexible
HVAC unit which is controlled in order to minimise costs, with the constraint
that the internal temperature remains between 16 and 18 degrees C.
"""

# import modules
import os
from os.path import normpath, join
import copy
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import numpy as np
import picos as pic
import matplotlib.pyplot as plt
from datetime import date, timedelta

import System.Assets as AS
import System.Markets as MK
import System.EnergySystem as ES

import sys

print('Code started.')
# plt.close('all')

############## VERSION ##############


__version__ = "1.1.0"


#######################################
###
### Case Study: Building HVAC flexibility
###
#######################################

def get_building_case_original_results(is_winter: bool):
    path_string = normpath('Results/Building_Case_Study/')
    if not os.path.isdir(path_string):
        os.makedirs(path_string)
    #######################################
    ### STEP 0: Load Data
    #######################################
    winter_photovoltaic_electricity_generation_data_path = os.path.join("Data/Building/", "PVpu_1min_2014JAN.csv")
    winter_photovoltaic_electricity_generation_in_per_unit = pd.read_csv(
        winter_photovoltaic_electricity_generation_data_path, index_col=0, parse_dates=True).values

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
    else:
        photovoltaic_generation_per_unit = sum_of_winter_photovoltaic_electricity_generation_in_per_unit / \
                                           np.max(sum_of_summer_photovoltaic_electricity_generation_in_per_unit)
    electric_loads = summer_electric_load_data
    #######################################
    ### STEP 1: setup parameters
    #######################################
    time_interval_in_minutes = 1
    time_interval_in_hours = time_interval_in_minutes / 60  # 1 minute time intervals
    hours_per_day = 24
    number_of_time_intervals_per_day = int(hours_per_day / time_interval_in_hours)  # Number of intervals

    energy_management_system_time_interval_in_minutes = 15      # 15 minute EMS time intervals
    energy_management_system_time_interval_in_hours = energy_management_system_time_interval_in_minutes / 60  # Number of EMS intervals
    number_of_energy_management_system_time_intervals_per_day = int(number_of_time_intervals_per_day *
                                                                    time_interval_in_hours /
                                                                    energy_management_system_time_interval_in_hours)
    building_reference_degree_celsius = 8  # from 8 am to 8 am
    rated_photovoltaic_kilowatts = 400  # power rating of the PV generation

    # Electric Vehicle (EV) parameters
    number_of_electric_vehicles = 120  # number of EVs
    max_electric_vehicle_energy_level = 30  # maximum EV energy level
    max_electric_vehicle_charging_power = 7  # maximum EV charging power

    np.random.seed(1000)
    random_electric_vehicle_energy_levels = max_electric_vehicle_energy_level * np.random.uniform(
        0, 1, number_of_electric_vehicles)  # random EV initial energy levels
    electric_vehicle_arrival_time_start = 12  # 12:00 pm
    electric_vehicle_arrival_time_end = 22  # 10:00 pm
    random_electric_vehicle_arrival_time = np.random.randint(electric_vehicle_arrival_time_start * 2,
                                                             electric_vehicle_arrival_time_end * 2,
                                                             number_of_electric_vehicles) - \
                                           building_reference_degree_celsius * 2
    electric_vehicle_departure_time_start = 29  # 05:00 am
    electric_vehicle_departure_time_end = 32  # 08:00 am
    random_electric_vehicle_departure_time = np.random.randint(electric_vehicle_departure_time_start * 2,
                                                               electric_vehicle_departure_time_end * 2 + 1,
                                                               number_of_electric_vehicles) - \
                                             building_reference_degree_celsius * 2
    # Ensure EVs can be feasibility charged
    for i in range(number_of_electric_vehicles):
        random_electric_vehicle_departure_time[i] = np.max([random_electric_vehicle_departure_time[i],
                                                            random_electric_vehicle_arrival_time[i]])
        random_electric_vehicle_energy_levels[i] = np.max([random_electric_vehicle_energy_levels[i],
                                                           max_electric_vehicle_energy_level -
                                                           max_electric_vehicle_charging_power *
                                                           (random_electric_vehicle_departure_time[i] -
                                                            random_electric_vehicle_arrival_time[i])])
    # Building parameters
    max_building_degree_celsius = 18
    min_building_degree_celsius = 16
    building_reference_degree_celsius = 17  # At the beginning of the scenario
    max_heat_kilowatts = 90
    max_cooling_kilowatts = 200
    hvac_heating_coefficient_of_performance = 3
    hvac_cooling_coefficient_of_performance = 1
    # Parameters from MultiSAVES
    C = 500  # kWh/ degree celsius
    R = 0.0337  # degree celsius/kW
    # Market parameters
    dt_market = energy_management_system_time_interval_in_hours  # market and EMS have the same time-series
    T_market = number_of_energy_management_system_time_intervals_per_day  # market and EMS have same length
    # TD: update from https://www.ofgem.gov.uk/publications/feed-tariff-fit-tariff-table-1-april-2021
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
    bus1 = pp.create_bus(network, vn_kv=20., name="bus 1")
    bus2 = pp.create_bus(network, vn_kv=0.4, name="bus 2")
    bus3 = pp.create_bus(network, vn_kv=0.4, name="bus 3")
    # create bus elements
    pp.create_ext_grid(network, bus=bus1, vm_pu=1.0, name="Grid Connection")
    # create branch elements
    trafo = pp.create_transformer(network, hv_bus=bus1, lv_bus=bus2, std_type="0.4 MVA 20/0.4 kV", name="Trafo")
    line = pp.create_line(network, from_bus=bus2, to_bus=bus3, length_km=0.1, std_type="NAYY 4x50 SE", name="Line")
    N_buses = network.bus['name'].size
    #######################################
    ### STEP 3: setup the assets
    #######################################
    # initiate empty lists for different types of assets
    storage_assets = []
    building_assets = []
    nondispatch_assets = []
    # PV source at bus 3
    Pnet = -photovoltaic_generation_per_unit * rated_photovoltaic_kilowatts  # 100kW PV plant
    Qnet = np.zeros(number_of_time_intervals_per_day)
    PV_gen_bus3 = AS.NondispatchableAsset(Pnet, Qnet, bus3, time_interval_in_hours, number_of_time_intervals_per_day)
    nondispatch_assets.append(PV_gen_bus3)
    # Load at bus 3
    Pnet = np.sum(electric_loads, 1)  # summed load across 120 households
    Qnet = np.zeros(number_of_time_intervals_per_day)
    load_bus3 = AS.NondispatchableAsset(Pnet, Qnet, bus3, time_interval_in_hours, number_of_time_intervals_per_day)
    nondispatch_assets.append(load_bus3)
    # Building asset at bus 3
    Tmax_bldg_i = max_building_degree_celsius * np.ones(number_of_energy_management_system_time_intervals_per_day)
    Tmin_bldg_i = min_building_degree_celsius * np.ones(number_of_energy_management_system_time_intervals_per_day)
    Hmax_bldg_i = max_heat_kilowatts
    Cmax_bldg_i = max_cooling_kilowatts
    T0_i = building_reference_degree_celsius
    C_i = C
    R_i = R
    CoP_heating_i = hvac_heating_coefficient_of_performance
    CoP_cooling_i = hvac_cooling_coefficient_of_performance
    if is_winter:
        Ta_i = 10 * np.ones(number_of_energy_management_system_time_intervals_per_day)
    else:
        Ta_i = 22 * np.ones(number_of_energy_management_system_time_intervals_per_day)
    bus_id_bldg_i = bus3
    bldg_i = AS.BuildingAsset(Tmax_bldg_i, Tmin_bldg_i, Hmax_bldg_i, Cmax_bldg_i, T0_i, C_i, R_i, CoP_heating_i,
                              CoP_cooling_i, Ta_i, bus_id_bldg_i, time_interval_in_hours, number_of_time_intervals_per_day, energy_management_system_time_interval_in_hours, number_of_energy_management_system_time_intervals_per_day)
    building_assets.append(bldg_i)
    N_BLDGs = len(building_assets)
    #######################################
    ### STEP 4: setup the market
    #######################################
    bus_id_market = bus1
    market = MK.Market(network_bus_id=bus_id_market,
                       number_of_EMS_time_intervals=number_of_energy_management_system_time_intervals_per_day,
                       export_prices_in_pounds_per_kWh=prices_export,
                       peak_period_import_prices=peak_period_import_prices,
                       peak_period_hours_per_day=peak_period_hours_per_day,
                       valley_period_import_prices=valley_period_import_prices,
                       valley_period_hours_per_day=valley_period_hours_per_day,
                       max_demand_charge_in_pounds_per_kWh=demand_charge,
                       max_import_kW=max_import_kW,
                       min_import_kW=min_import_kW,
                       minutes_market_interval=dt_market,
                       number_of_market_time_intervals=T_market,
                       offered_kW_in_frequency_response=offered_kW_in_frequency_response,
                       max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                       min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                       frequency_response_price_in_pounds_per_kWh=frequency_response_price_in_pounds_per_kWh,
                       daily_connection_charge=daily_connection_charge)

    #######################################
    # STEP 5: setup the energy system
    #######################################
    energy_system = ES.EnergySystem(storage_assets, nondispatch_assets, network, market, time_interval_in_hours, number_of_time_intervals_per_day, energy_management_system_time_interval_in_hours, number_of_energy_management_system_time_intervals_per_day,
                                    building_assets)
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
    for i in range(len(nondispatch_assets)):
        bus_id = nondispatch_assets[i].bus_id
        P_demand_base += nondispatch_assets[i].Pnet
    #######################################
    ### STEP 7: plot results
    #######################################
    # x-axis time values
    time = time_interval_in_hours * np.arange(number_of_time_intervals_per_day)
    time_ems = energy_management_system_time_interval_in_hours * np.arange(number_of_energy_management_system_time_intervals_per_day)
    timeE = time_interval_in_hours * np.arange(number_of_time_intervals_per_day + 1)
    # Print revenue generated
    revenue = market._calculate_revenue(-Pnet_market, time_interval_in_hours)

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
