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

def get_winter_building_case_original_results():
    path_string = normpath('Results/Building_Case_Study/')
    if not os.path.isdir(path_string):
        os.makedirs(path_string)
    #######################################
    ### STEP 0: Load Data
    #######################################
    choice = 1  # Summer
    PV_data_path = os.path.join("Data/Building/", "PVpu_1min_2014JAN.csv")
    PVpu_raw_wtr = pd.read_csv(PV_data_path, index_col=0, parse_dates=True).values
    Loads_data_path = os.path.join("Data/Building/", "Loads_1min_2014JAN.csv")
    Loads_raw_wtr = pd.read_csv(Loads_data_path, index_col=0, parse_dates=True).values
    PV_data_path = os.path.join("Data/Building/", "PVpu_1min_2013JUN.csv")
    PVpu_raw_smr = pd.read_csv(PV_data_path, index_col=0, parse_dates=True).values
    Loads_data_path = os.path.join("Data/Building/", "Loads_1min_2013JUN.csv")
    Loads_raw_smr = pd.read_csv(Loads_data_path, index_col=0, parse_dates=True).values
    PVtotal_smr = np.sum(PVpu_raw_smr, 1)
    PVtotal_wtr = np.sum(PVpu_raw_wtr, 1)
    winterFlag = True
    if winterFlag == False:
        PVpu = PVtotal_smr / np.max(PVtotal_smr)
    else:
        PVpu = PVtotal_wtr / np.max(PVtotal_smr)
    Loads = Loads_raw_smr
    #######################################
    ### STEP 1: setup parameters
    #######################################
    dt = 1 / 60  # 1 minute time intervals
    T = int(24 / dt)  # Number of intervals
    dt_ems = 15 / 60  # 30 minute EMS time intervals
    T_ems = int(T * dt / dt_ems)  # Number of EMS intervals
    T0 = 8  # from 8 am to 8 am
    Ppv_nom = 400  # power rating of the PV generation
    # Electric Vehicle (EV) parameters
    N_EVs = 120  # number of EVs
    Emax_EV = 30  # maximum EV energy level
    Emin_EV = 0  # minimum EV energy level
    P_max_EV = 7  # maximum EV charging power
    P_min_EV = 0  # minimum EV charging power
    np.random.seed(1000)
    E0_EVs = Emax_EV * np.random.uniform(0, 1, N_EVs)  # random EV initial energy levels
    ta_EVs = np.random.randint(12 * 2, 22 * 2, N_EVs) - T0 * 2  # random EV arrival times between 12pm and 10pm
    td_EVs = np.random.randint(29 * 2, 32 * 2 + 1, N_EVs) - T0 * 2  # random EV departure times 5am and 8am
    # Ensure EVs can be feasibility charged
    for i in range(N_EVs):
        td_EVs[i] = np.max([td_EVs[i], ta_EVs[i]])
        E0_EVs[i] = np.max([E0_EVs[i], Emax_EV - P_max_EV * (td_EVs[i] - ta_EVs[i])])
    # Building parameters
    Tmax = 18  # degree celsius
    Tmin = 16  # degree celsius
    T0 = 17  # degree centigrade
    heatmax = 90  # kW Max heat supplied
    coolmax = 200  # kW Max cooling
    CoP_heating = 3  # coefficient of performance - heating
    CoP_cooling = 1  # coefficient of performance - cooling
    # Parameters from MultiSAVES
    C = 500  # kWh/ degree celsius
    R = 0.0337  # degree celsius/kW
    # Market parameters
    dt_market = dt_ems  # market and EMS have the same time-series
    T_market = T_ems  # market and EMS have same length
    # TD: update from https://www.ofgem.gov.uk/publications/feed-tariff-fit-tariff-table-1-april-2021
    prices_export = 0.04  # money received of net exports
    peak_period_import_prices = 0.07
    peak_period_hours_per_day = 7
    valley_period_import_prices = 0.15
    valley_period_hours_per_day = 17

    demand_charge = 0.10  # price per kW for the maximum demand
    Pmax_market = 500 * np.ones(T_market)  # maximum import power
    Pmin_market = -500 * np.ones(T_market)  # maximum export power

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
    Pnet = -PVpu * Ppv_nom  # 100kW PV plant
    Qnet = np.zeros(T)
    PV_gen_bus3 = AS.NondispatchableAsset(Pnet, Qnet, bus3, dt, T)
    nondispatch_assets.append(PV_gen_bus3)
    # Load at bus 3
    Pnet = np.sum(Loads, 1)  # summed load across 120 households
    Qnet = np.zeros(T)
    load_bus3 = AS.NondispatchableAsset(Pnet, Qnet, bus3, dt, T)
    nondispatch_assets.append(load_bus3)
    # Building asset at bus 3
    Tmax_bldg_i = Tmax * np.ones(T_ems)
    Tmin_bldg_i = Tmin * np.ones(T_ems)
    Hmax_bldg_i = heatmax
    Cmax_bldg_i = coolmax
    T0_i = T0
    C_i = C
    R_i = R
    CoP_heating_i = CoP_heating
    CoP_cooling_i = CoP_cooling
    if winterFlag == True:
        Ta_i = 10 * np.ones(T_ems)
    else:
        Ta_i = 22 * np.ones(T_ems)
    bus_id_bldg_i = bus3
    bldg_i = AS.BuildingAsset(Tmax_bldg_i, Tmin_bldg_i, Hmax_bldg_i, Cmax_bldg_i, T0_i, C_i, R_i, CoP_heating_i,
                              CoP_cooling_i, Ta_i, bus_id_bldg_i, dt, T, dt_ems, T_ems)
    building_assets.append(bldg_i)
    N_BLDGs = len(building_assets)
    #######################################
    ### STEP 4: setup the market
    #######################################
    bus_id_market = bus1
    market = MK.Market(network_bus_id=bus_id_market,
                       number_of_EMS_time_intervals=T_ems,
                       export_prices_in_pounds_per_kWh=prices_export,
                       peak_period_import_prices=peak_period_import_prices,
                       peak_period_hours_per_day=peak_period_hours_per_day,
                       valley_period_import_prices=valley_period_import_prices,
                       valley_period_hours_per_day=valley_period_hours_per_day,
                       max_demand_charge_in_pounds_per_kWh=demand_charge,
                       max_import_kW=Pmax_market,
                       min_import_kW=Pmin_market,
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
    energy_system = ES.EnergySystem(storage_assets, nondispatch_assets, network, market, dt, T, dt_ems, T_ems,
                                    building_assets)
    #######################################
    ### STEP 6: simulate the energy system:
    #######################################
    output = energy_system.simulate_network()
    # output = energy_system.simulate_network_bldg()
    buses_Vpu = output['buses_Vpu']
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
    P_demand_base = np.zeros(T)
    for i in range(len(nondispatch_assets)):
        bus_id = nondispatch_assets[i].bus_id
        P_demand_base += nondispatch_assets[i].Pnet
    #######################################
    ### STEP 7: plot results
    #######################################
    # x-axis time values
    time = dt * np.arange(T)
    time_ems = dt_ems * np.arange(T_ems)
    timeE = dt * np.arange(T + 1)
    # Print revenue generated
    revenue = market._calculate_revenue(-Pnet_market, dt)

    return [revenue,
            buses_Vpu[0],
            buses_Vang[0],
            buses_Pnet[0],
            buses_Qnet[0],
            Pnet_market[0],
            Qnet_market[0],
            buses_Vpu[0],
            P_import_ems[0],
            P_export_ems[0],
            P_BLDG_ems[0],
            P_demand_ems[0],
            P_demand_base[0]]
