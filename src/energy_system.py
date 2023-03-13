#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPEN Energy src Module.

The EnergySystem Class has two types of methods
i) energy management system (EMS) methods which implement algorithms to
calculate Asset control references, and
ii) simulation methods which call an EMS method to obtain control
references for Asset objects, update the state of Asset objects by calling
their updatecontrol method and update the state of the Network by calling
its power flow method.
An EnergySystem has two separate time series, one for the EMS, and the
other for simulation.

OPEN includes two EMS methods for controllable Asset objects:
(i) one for multi-period optimisation
with a simple ‘copper plate’ network model, and
(ii) one for multi-period optimisation with a linear multi-phase
distribution network model which includes voltage and current flow
constraints.

Open has simulation methods for:
(i) open-loop optimisation, where the EMS method is run ahead of operation
to obtain controllable Asset references over the EMS time-series; and
(ii) for MPC, where the EMS method is implemented with a receding horizon
so that the flexible Asset references are updated at each step of the EMS
time series.
"""

import copy
import datetime
from typing import List
import pandapower as pp
import numpy as np
import picos as pic
from picos import RealVariable
from src.assets import NonDispatchableAsset, StorageAsset
from src.markets import Market
from src.network_3_phase_pf import ThreePhaseNetwork
from src.time_intervals import get_number_of_time_intervals_per_day


def get_temperature_constraint_for_no_initial_time(alpha: float, beta: float, gamma: float,
                                                   previous_building_internal_temperature_in_celsius_degrees: float,
                                                   chiller_coefficient_of_performance: float,
                                                   previous_cooling_active_power_in_kilowatts: float,
                                                   heat_pump_coefficient_of_performance: float,
                                                   previous_heating_active_power_in_kilowatts: float,
                                                   previous_ambient_temperature_in_degree_celsius: float):
    temperature_constraint = \
        alpha * previous_building_internal_temperature_in_celsius_degrees \
        - beta * chiller_coefficient_of_performance * previous_cooling_active_power_in_kilowatts \
        + beta * heat_pump_coefficient_of_performance * previous_heating_active_power_in_kilowatts \
        + gamma * previous_ambient_temperature_in_degree_celsius

    return temperature_constraint


class EnergySystem:

    def __init__(self,
                 storage_assets: List[StorageAsset],
                 non_dispatchable_assets: List[NonDispatchableAsset],
                 network: ThreePhaseNetwork,
                 market: Market,
                 simulation_time_series_resolution_in_hours: float,
                 energy_management_system_time_series_resolution_in_hours: float,
                 building_assets: List):

        self.storage_assets = storage_assets
        self.non_dispatchable_assets = non_dispatchable_assets
        self.network = network
        self.market = market
        self.simulation_time_series_resolution_in_hours = simulation_time_series_resolution_in_hours
        self.energy_management_system_time_series_resolution_in_hours = \
            energy_management_system_time_series_resolution_in_hours
        self.building_assets = building_assets

        self.number_of_time_intervals_per_day = get_number_of_time_intervals_per_day(
            time_series_resolution_in_hours=self.simulation_time_series_resolution_in_hours)
        self.number_of_energy_management_system_time_intervals_per_day = get_number_of_time_intervals_per_day(
            time_series_resolution_in_hours=self.energy_management_system_time_series_resolution_in_hours)

    def _get_non_dispatchable_assets_active_power_in_kilowatts(self):
        return sum([non_dispatchable_asset.active_power_in_kilowatts for non_dispatchable_asset in
                    self.non_dispatchable_assets])

    def _resample_non_dispatchable_assets_active_power_in_kilowatts(self,
                                                                    non_dispatchable_assets_active_power_in_kilowatts):
        demand_active_power_in_kilowatts_for_the_energy_management_system = \
            np.zeros(self.number_of_energy_management_system_time_intervals_per_day)
        for t_ems in range(self.number_of_energy_management_system_time_intervals_per_day):
            t_indexes = (t_ems * self.energy_management_system_time_series_resolution_in_hours /
                         self.simulation_time_series_resolution_in_hours \
                         + np.arange(0, self.energy_management_system_time_series_resolution_in_hours /
                                     self.simulation_time_series_resolution_in_hours)).astype(int)
            demand_active_power_in_kilowatts_for_the_energy_management_system[t_ems] = \
                np.mean(non_dispatchable_assets_active_power_in_kilowatts[t_indexes])
        return demand_active_power_in_kilowatts_for_the_energy_management_system

    # Open Loop Control Methods
    def run_single_copper_plate_network_optimization_model(self):
        """
        Energy management system optimization assuming all assets connected to
        a single node.

        Parameters
        ----------
        self : EnergySystem object
            Object containing information on assets, market, network and time
            resolution.

        Returns
        -------
        Output : dictionary
            The following numpy.ndarrays are present depending upon asset mix:
                P_ES_val : Charge/discharge power for storage assets (kW)
                P_BLDG_val :Builfing power consumption (kW)
                active_power_imports_in_kilowatts :Power imported from central grid (kW)
                active_power_exports_in_kilowatts :Power exported to central grid (kW)
                resampled_non_dispatchable_assets_active_power_in_kilowatts :src power demand at energy management time
                              resolution

        """
        # setup and run a basic energy optimisation
        # (single copper plate network model)
        # STEP 0: setup variables
        problem = pic.Problem()

        number_of_storage_assets = len(self.storage_assets)
        number_of_buildings = len(self.building_assets)
        number_of_dispatchable_assets = number_of_storage_assets + number_of_buildings

        non_dispatchable_assets_active_power_in_kilowatts = \
            self._get_non_dispatchable_assets_active_power_in_kilowatts()
        resampled_non_dispatchable_assets_active_power_in_kilowatts = \
            self._resample_non_dispatchable_assets_active_power_in_kilowatts(
                non_dispatchable_assets_active_power_in_kilowatts=non_dispatchable_assets_active_power_in_kilowatts)

        # STEP 1: set up decision variables
        controllable_assets_active_power_in_kilowatts = RealVariable(
            name='controllable_assets_active_power_in_kilowatts',
            shape=(self.number_of_energy_management_system_time_intervals_per_day, number_of_dispatchable_assets),
            lower=0)
        for number_of_building in np.arange(0, number_of_buildings):
            cooling_active_power_in_kilowatts = RealVariable(
                name='cooling_active_power_in_kilowatts',
                shape=(self.number_of_energy_management_system_time_intervals_per_day, number_of_buildings),
                lower=0, upper=self.building_assets[number_of_building].max_consumed_electric_cooling_kilowatts)
            heating_active_power_in_kilowatts = RealVariable(
                name='heating_active_power_in_kilowatts',
                shape=(self.number_of_energy_management_system_time_intervals_per_day, number_of_buildings),
                lower=0, upper=self.building_assets[number_of_building].max_consumed_electric_heating_kilowatts)
            building_internal_temperature_in_celsius_degrees = RealVariable(
                name='building_internal_temperature_in_celsius_degrees',
                shape=(self.number_of_energy_management_system_time_intervals_per_day, number_of_buildings),
                lower=self.building_assets[number_of_building].min_inside_degree_celsius,
                upper=self.building_assets[number_of_building].max_inside_degree_celsius)

        active_power_imports_in_kilowatts = RealVariable(
            name='active_power_imports_in_kilowatts',
            shape=(self.number_of_energy_management_system_time_intervals_per_day, 1),
            lower=0, upper=self.market.max_import_kilowatts)
        active_power_exports_in_kilowatts = RealVariable(
            name='active_power_exports_in_kilowatts',
            shape=(self.number_of_energy_management_system_time_intervals_per_day, 1),
            lower=0, upper=self.market.max_import_kilowatts)
        # (positive) maximum demand dummy variable
        max_active_power_demand_in_kilowatts = RealVariable(
            name='max_active_power_demand_in_kilowatts', shape=1, lower=0)
        # STEP 2: set up constraints
        asum_np = np.tril(np.ones([self.number_of_energy_management_system_time_intervals_per_day,
                                   self.number_of_energy_management_system_time_intervals_per_day])).astype('double')
        # lower triangle matrix summing powers
        asum = pic.Constant('asum', asum_np)

        self.add_linear_building_thermal_model_constraints_to_the_problem(
            number_of_buildings=number_of_buildings, problem=problem,
            heating_active_power_in_kilowatts=heating_active_power_in_kilowatts,
            cooling_active_power_in_kilowatts=cooling_active_power_in_kilowatts,
            building_internal_temperature_in_celsius_degrees=building_internal_temperature_in_celsius_degrees,
            controllable_assets_active_power_in_kilowatts=controllable_assets_active_power_in_kilowatts)

        self.add_linear_battery_model_constraints_to_the_problem(
            number_of_storage_assets=number_of_storage_assets, problem=problem,
            controllable_assets_active_power_in_kilowatts=controllable_assets_active_power_in_kilowatts,
            number_of_buildings=number_of_buildings, asum=asum)

        self.add_import_and_export_constraints_to_the_problem(
            problem=problem,
            controllable_assets_active_power_in_kilowatts=controllable_assets_active_power_in_kilowatts,
            resampled_non_dispatchable_assets_active_power_in_kilowatts=
            resampled_non_dispatchable_assets_active_power_in_kilowatts,
            active_power_imports_in_kilowatts=active_power_imports_in_kilowatts,
            active_power_exports_in_kilowatts=active_power_exports_in_kilowatts,
            max_active_power_demand_in_kilowatts=max_active_power_demand_in_kilowatts)

        self.add_frequency_response_constraints_to_the_problem(
            number_of_storage_assets=number_of_storage_assets, problem=problem, asum=asum,
            controllable_assets_active_power_in_kilowatts=controllable_assets_active_power_in_kilowatts,
            number_of_buildings=number_of_buildings)

        # STEP 3: set up objective
        max_demand_charge_in_euros = \
            self.market.max_demand_charge_in_euros_per_kWh * max_active_power_demand_in_kilowatts

        import_and_export_cost_in_euros = sum(
            self.market.import_prices_in_euros_per_kilowatt_hour[t] * active_power_imports_in_kilowatts[t]
            - self.market.export_price_time_series_in_euros_per_kWh[t]  # Negative as it is a profit
            * active_power_exports_in_kilowatts[t]
            for t in range(self.number_of_energy_management_system_time_intervals_per_day))

        expression = max_demand_charge_in_euros + import_and_export_cost_in_euros
        problem.set_objective(direction='min', expression=expression)

        # STEP 4: solve the optimisation

        print('*** SOLVING THE OPTIMISATION PROBLEM ***')
        optimization_start_time = datetime.datetime.now()
        problem.solve(verbosity=0)
        optimization_end_time = datetime.datetime.now()
        optimization_time = optimization_end_time - optimization_start_time
        print('*** OPTIMISATION COMPLETE ***')
        print('*** OPTIMISATION TIME: ', optimization_time, '***')

        controllable_assets_active_power_in_kilowatts = controllable_assets_active_power_in_kilowatts.value
        active_power_imports_in_kilowatts = active_power_imports_in_kilowatts.value
        active_power_exports_in_kilowatts = active_power_exports_in_kilowatts.value
        resampled_non_dispatchable_assets_active_power_in_kilowatts = \
            resampled_non_dispatchable_assets_active_power_in_kilowatts

        if number_of_buildings > 0:
            # Store internal temperature inside object
            building_internal_temperature_in_celsius_degrees = building_internal_temperature_in_celsius_degrees.value
            for number_of_building in range(number_of_buildings):
                self.building_assets[number_of_building].building_internal_temperature_in_celsius_degrees = \
                    building_internal_temperature_in_celsius_degrees[:, number_of_building]

        active_power_consumed_by_the_buildings_in_kilowatts = \
            controllable_assets_active_power_in_kilowatts[:, :number_of_buildings]
        if number_of_storage_assets > 0 and number_of_buildings > 0:
            output = {
                'active_power_consumed_by_the_buildings_in_kilowatts':
                    active_power_consumed_by_the_buildings_in_kilowatts,
                'charge_discharge_power_for_storage_assets_in_kilowatts':
                    controllable_assets_active_power_in_kilowatts[
                    :, number_of_buildings:number_of_storage_assets + number_of_buildings],
                'active_power_imports_in_kilowatts': active_power_imports_in_kilowatts,
                'active_power_exports_in_kilowatts': active_power_exports_in_kilowatts,
                'resampled_non_dispatchable_assets_active_power_in_kilowatts':
                    resampled_non_dispatchable_assets_active_power_in_kilowatts}
        elif number_of_storage_assets == 0 and number_of_buildings > 0:
            output = {'active_power_consumed_by_the_buildings_in_kilowatts':
                          active_power_consumed_by_the_buildings_in_kilowatts,
                      'active_power_imports_in_kilowatts': active_power_imports_in_kilowatts,
                      'active_power_exports_in_kilowatts': active_power_exports_in_kilowatts,
                      'resampled_non_dispatchable_assets_active_power_in_kilowatts':
                          resampled_non_dispatchable_assets_active_power_in_kilowatts}
        elif number_of_storage_assets > 0 and number_of_buildings == 0:
            output = {
                'charge_discharge_power_for_storage_assets_in_kilowatts': controllable_assets_active_power_in_kilowatts[
                                                                          :, :number_of_storage_assets],
                'active_power_imports_in_kilowatts': active_power_imports_in_kilowatts,
                'active_power_exports_in_kilowatts': active_power_exports_in_kilowatts,
                'resampled_non_dispatchable_assets_active_power_in_kilowatts':
                    resampled_non_dispatchable_assets_active_power_in_kilowatts}
        else:
            raise ValueError('No dispatchable assets.')

        return output

    def simulate_network(self):
        """
        Run the Energy Management src in open loop and simulate a pandapower
        network.

        Parameters
        ----------
        self : EnergySystem object
            Object containing information on assets, market, network and time
            resolution.

        Returns
        -------
        Output : dictionary
            The following numpy.ndarrays are present depending upon asset mix:
                buses_Vpu : Voltage magnitude at bus (V)
                buses_voltage_angle_in_degrees : Voltage angle at bus (rad)
                buses_active_power_in_kilowatts : Real power at bus (kW)
                buses_reactive_power_in_kilovolt_ampere_reactive : Reactive power at bus (kVAR)
                market_active_power_in_kilowatts : Real power seen by the market (kW)
                market_reactive_power_in_kilovolt_ampere_reactive : Reactive power seen by the market (kVAR)
                storage_asset_charge_or_discharge_power_in_kilowatts : Charge/discharge power for storage assets at energy
                    management time resolution (kW)
                building_power_consumption_in_kilowatts :Builfing power consumption at energy management
                    time resolution (kW)
                imported_active_power_in_kilowatts :Power imported from central grid at energy
                    management time resolution (kW)
                exported_active_power_in_kilowatts :Power exported to central grid at energy
                    management time resolution(kW)
                P_demand_ems :src power demand at energy management time
                    resolution (kW)

        """
        # STEP 1: solve the optimisation
        energy_management_system_output = self.run_single_copper_plate_network_optimization_model()

        number_of_storage_assets = len(self.storage_assets)
        number_of_buildings = len(self.building_assets)
        number_of_non_dispatchable_assets = len(self.non_dispatchable_assets)

        imported_active_power_in_kilowatts = energy_management_system_output['active_power_imports_in_kilowatts']
        exported_active_power_in_kilowatts = energy_management_system_output['active_power_exports_in_kilowatts']
        if number_of_storage_assets > 0:
            storage_asset_charge_or_discharge_power_in_kilowatts = \
                energy_management_system_output['charge_discharge_power_for_storage_assets_in_kilowatts']
        if number_of_buildings > 0:
            building_power_consumption_in_kilowatts = \
                energy_management_system_output['active_power_consumed_by_the_buildings_in_kilowatts']
        active_power_demand_in_kilowatts = \
            energy_management_system_output['resampled_non_dispatchable_assets_active_power_in_kilowatts']
        # convert P_ES and P_BLDG signals to system time-series scale
        if number_of_storage_assets > 0:
            electric_vehicle_fleet_active_power_in_kilowatts = \
                self._get_asset_active_power_in_kilowatts(
                    number_of_assets=number_of_storage_assets,
                    active_power_in_kilowatts=
                    storage_asset_charge_or_discharge_power_in_kilowatts)
        if number_of_buildings > 0:
            buildings_active_power_in_kilowatts = \
                self._get_asset_active_power_in_kilowatts(
                    number_of_assets=number_of_buildings,
                    active_power_in_kilowatts=building_power_consumption_in_kilowatts)

        # STEP 2: update the controllable assets
        if number_of_storage_assets > 0:
            for i in range(number_of_storage_assets):
                self.storage_assets[i].update_control(electric_vehicle_fleet_active_power_in_kilowatts[:, i])
        if number_of_buildings > 0:
            for i in range(number_of_buildings):
                self.building_assets[i].update_control(buildings_active_power_in_kilowatts[:, i])

        # STEP 3: simulate the network
        number_of_buses = self.network.bus['name'].size
        active_power_bus_demand_in_kilowatts = np.zeros([self.number_of_time_intervals_per_day, number_of_buses])
        reactive_power_bus_demand_in_kilovolt_ampere_reactive = \
            np.zeros([self.number_of_time_intervals_per_day, number_of_buses])
        if number_of_storage_assets > 0:
            # calculate the total real and reactive power demand at each bus
            for i in range(number_of_storage_assets):
                non_dispatchable_assets_bus_id = self.storage_assets[i].bus_id
                active_power_bus_demand_in_kilowatts[:, non_dispatchable_assets_bus_id] += \
                    self.storage_assets[i].active_power_in_kilowatts
        if number_of_buildings > 0:
            # calculate the total real and reactive power demand at each bus
            for i in range(number_of_buildings):
                building_bus_id = self.building_assets[i].bus_id
                active_power_bus_demand_in_kilowatts[:, building_bus_id] += \
                    self.building_assets[i].active_power_in_kilowatts
                reactive_power_bus_demand_in_kilovolt_ampere_reactive[:, building_bus_id] += self.building_assets[
                    i].reactive_power
        for i in range(number_of_non_dispatchable_assets):
            non_dispatchable_assets_bus_id = self.non_dispatchable_assets[i].bus_id
            active_power_bus_demand_in_kilowatts[:, non_dispatchable_assets_bus_id] += \
                self.non_dispatchable_assets[i].active_power_in_kilowatts
            reactive_power_bus_demand_in_kilovolt_ampere_reactive[:, non_dispatchable_assets_bus_id] += \
                self.non_dispatchable_assets[i].reactive_power

        buses_voltage_in_per_unit = np.zeros([self.number_of_time_intervals_per_day, number_of_buses])
        buses_voltage_angle_in_degrees = np.zeros([self.number_of_time_intervals_per_day, number_of_buses])
        buses_active_power_in_kilowatts = np.zeros([self.number_of_time_intervals_per_day, number_of_buses])
        buses_reactive_power_in_kilovolt_ampere_reactive = np.zeros([self.number_of_time_intervals_per_day,
                                                                     number_of_buses])
        market_active_power_in_kilowatts = np.zeros(self.number_of_time_intervals_per_day)
        market_reactive_power_in_kilovolt_ampere_reactive = np.zeros(self.number_of_time_intervals_per_day)

        simulation_start_time = datetime.datetime.now()
        print('*** SIMULATING THE NETWORK ***')
        for number_of_time_interval_per_day in range(self.number_of_time_intervals_per_day):
            # for each time interval:
            # set up a copy of the network for simulation interval number_of_time_interval_per_day
            network_copy = copy.deepcopy(self.network)
            for non_dispatchable_assets_bus_id in range(number_of_buses):
                specific_active_power_bus_demand_in_kilowatts = \
                    active_power_bus_demand_in_kilowatts[
                        number_of_time_interval_per_day, non_dispatchable_assets_bus_id]
                specific_reactive_power_bus_demand_in_kilovolt_ampere_reactive = \
                    reactive_power_bus_demand_in_kilovolt_ampere_reactive[number_of_time_interval_per_day,
                    non_dispatchable_assets_bus_id]
                # add P,Q loads to the network copy
                pp.create_load(network_copy, non_dispatchable_assets_bus_id,
                               specific_active_power_bus_demand_in_kilowatts / 1e3,
                               specific_reactive_power_bus_demand_in_kilovolt_ampere_reactive / 1e3)
            # run the power flow simulation
            max_iteration = 100
            pp.runpp(net=network_copy, max_iteration=max_iteration)  # or “nr”

            if number_of_time_interval_per_day % 100 == 0:
                print('network simulation complete for number_of_time_interval_per_day = '
                      + str(number_of_time_interval_per_day) + ' of ' + str(self.number_of_time_intervals_per_day))
            market_active_power_in_kilowatts[number_of_time_interval_per_day] = \
                network_copy.res_ext_grid['p_mw'][0] * 1e3
            market_reactive_power_in_kilovolt_ampere_reactive[number_of_time_interval_per_day] = \
                network_copy.res_ext_grid['q_mvar'][0] * 1e3
            for number_of_bus in range(number_of_buses):
                buses_voltage_in_per_unit[number_of_time_interval_per_day, number_of_bus] = \
                    network_copy.res_bus['vm_pu'][number_of_bus]
                buses_voltage_angle_in_degrees[number_of_time_interval_per_day, number_of_bus] = \
                    network_copy.res_bus['va_degree'][number_of_bus]
                buses_active_power_in_kilowatts[number_of_time_interval_per_day, number_of_bus] = \
                    network_copy.res_bus['p_mw'][number_of_bus] * 1e3
                buses_reactive_power_in_kilovolt_ampere_reactive[number_of_time_interval_per_day, number_of_bus] = \
                    network_copy.res_bus['q_mvar'][number_of_bus] * 1e3

        print('*** NETWORK SIMULATION COMPLETE ***')
        simulation_end_time = datetime.datetime.now()
        simulation_time = simulation_end_time - simulation_start_time
        print('*** SIMULATION TIME: ', simulation_time, '***')

        if number_of_storage_assets > 0 and number_of_buildings > 0:
            output = {'buses_voltage_in_per_unit': buses_voltage_in_per_unit,
                      'buses_voltage_angle_in_degrees': buses_voltage_angle_in_degrees,
                      'buses_active_power_in_kilowatts': buses_active_power_in_kilowatts,
                      'buses_reactive_power_in_kilovolt_ampere_reactive':
                          buses_reactive_power_in_kilovolt_ampere_reactive,
                      'market_active_power_in_kilowatts': market_active_power_in_kilowatts,
                      'market_reactive_power_in_kilovolt_ampere_reactive':
                          market_reactive_power_in_kilovolt_ampere_reactive,
                      'storage_asset_charge_or_discharge_power_in_kilowatts':
                          storage_asset_charge_or_discharge_power_in_kilowatts,
                      'building_power_consumption_in_kilowatts': building_power_consumption_in_kilowatts,
                      'imported_active_power_in_kilowatts': imported_active_power_in_kilowatts,
                      'exported_active_power_in_kilowatts': exported_active_power_in_kilowatts,
                      'active_power_demand_in_kilowatts': active_power_demand_in_kilowatts}
        elif number_of_storage_assets == 0 and number_of_buildings > 0:
            output = {'buses_voltage_in_per_unit': buses_voltage_in_per_unit,
                      'buses_voltage_angle_in_degrees': buses_voltage_angle_in_degrees,
                      'buses_active_power_in_kilowatts': buses_active_power_in_kilowatts,
                      'buses_reactive_power_in_kilovolt_ampere_reactive':
                          buses_reactive_power_in_kilovolt_ampere_reactive,
                      'market_active_power_in_kilowatts': market_active_power_in_kilowatts,
                      'market_reactive_power_in_kilovolt_ampere_reactive':
                          market_reactive_power_in_kilovolt_ampere_reactive,
                      'building_power_consumption_in_kilowatts': building_power_consumption_in_kilowatts,
                      'imported_active_power_in_kilowatts': imported_active_power_in_kilowatts,
                      'exported_active_power_in_kilowatts': exported_active_power_in_kilowatts,
                      'active_power_demand_in_kilowatts': active_power_demand_in_kilowatts}
        elif number_of_storage_assets > 0 and number_of_buildings == 0:
            output = {'buses_voltage_in_per_unit': buses_voltage_in_per_unit,
                      'buses_voltage_angle_in_degrees': buses_voltage_angle_in_degrees,
                      'buses_active_power_in_kilowatts': buses_active_power_in_kilowatts,
                      'buses_reactive_power_in_kilovolt_ampere_reactive':
                          buses_reactive_power_in_kilovolt_ampere_reactive,
                      'market_active_power_in_kilowatts': market_active_power_in_kilowatts,
                      'market_reactive_power_in_kilovolt_ampere_reactive':
                          market_reactive_power_in_kilovolt_ampere_reactive,
                      'storage_asset_charge_or_discharge_power_in_kilowatts':
                          storage_asset_charge_or_discharge_power_in_kilowatts,
                      'imported_active_power_in_kilowatts': imported_active_power_in_kilowatts,
                      'exported_active_power_in_kilowatts': exported_active_power_in_kilowatts,
                      'active_power_demand_in_kilowatts': active_power_demand_in_kilowatts}
        else:
            raise ValueError('No dispatchable assets.')

        return output

    def _get_asset_active_power_in_kilowatts(self, number_of_assets: int,
                                             active_power_in_kilowatts):
        initial_active_power_in_kilowatts = np.zeros([self.number_of_time_intervals_per_day,
                                                      number_of_assets])
        for t in range(self.number_of_time_intervals_per_day):
            t_ems = int(t / (
                    self.energy_management_system_time_series_resolution_in_hours /
                    self.simulation_time_series_resolution_in_hours))
            initial_active_power_in_kilowatts[t, :] = \
                active_power_in_kilowatts[t_ems, :]
        return initial_active_power_in_kilowatts

    def add_linear_building_thermal_model_constraints_to_the_problem(
            self, number_of_buildings: int, problem: pic.Problem, heating_active_power_in_kilowatts: float,
            cooling_active_power_in_kilowatts: float, building_internal_temperature_in_celsius_degrees: float,
            controllable_assets_active_power_in_kilowatts: float):

        # linear building thermal model constraints
        for number_of_building in range(number_of_buildings):
            max_heating_power_constraint_in_kilowatts = \
                heating_active_power_in_kilowatts[:, number_of_building] <= \
                self.building_assets[number_of_building].max_consumed_electric_heating_kilowatts
            problem.add_constraint(max_heating_power_constraint_in_kilowatts)
            max_cooling_power_constraint_in_kilowatts = \
                cooling_active_power_in_kilowatts[:, number_of_building] <= \
                self.building_assets[number_of_building].max_consumed_electric_cooling_kilowatts
            problem.add_constraint(max_cooling_power_constraint_in_kilowatts)

            max_inside_degree_celsius_constraint = \
                building_internal_temperature_in_celsius_degrees[:, number_of_building] <= \
                self.building_assets[number_of_building].max_inside_degree_celsius
            problem.add_constraint(max_inside_degree_celsius_constraint)
            min_inside_degree_celsius_constraint = \
                building_internal_temperature_in_celsius_degrees[:, number_of_building] >= \
                self.building_assets[number_of_building].min_inside_degree_celsius
            problem.add_constraint(min_inside_degree_celsius_constraint)
            # power consumption is the sum of heating and cooling
            cooling_and_heating_active_power_in_kilowatts = \
                cooling_active_power_in_kilowatts[:, number_of_building] + \
                heating_active_power_in_kilowatts[:, number_of_building]
            cooling_and_heating_active_power_constraint_in_kilowatts = \
                controllable_assets_active_power_in_kilowatts[:, number_of_building] == \
                cooling_and_heating_active_power_in_kilowatts
            problem.add_constraint(cooling_and_heating_active_power_constraint_in_kilowatts)

            self.add_temperature_constraints_to_problem(number_of_building=number_of_building, problem=problem,
                                                        building_internal_temperature_in_celsius_degrees=
                                                        building_internal_temperature_in_celsius_degrees,
                                                        cooling_active_power_in_kilowatts=
                                                        cooling_active_power_in_kilowatts,
                                                        heating_active_power_in_kilowatts=
                                                        heating_active_power_in_kilowatts)

    def add_temperature_constraints_to_problem(self, number_of_building: int, problem: pic.Problem,
                                               building_internal_temperature_in_celsius_degrees: float,
                                               cooling_active_power_in_kilowatts: float,
                                               heating_active_power_in_kilowatts: float):

        alpha = self.building_assets[number_of_building].alpha
        beta = self.building_assets[number_of_building].beta
        gamma = self.building_assets[number_of_building].gamma

        for energy_management_system_time_interval_per_day in range(
                self.number_of_energy_management_system_time_intervals_per_day):
            if energy_management_system_time_interval_per_day == 0:
                # initial temperature constraint
                initial_inside_degree_celsius_constraint = \
                    building_internal_temperature_in_celsius_degrees[
                        energy_management_system_time_interval_per_day, number_of_building] == \
                    self.building_assets[number_of_building].initial_inside_degree_celsius
                problem.add_constraint(initial_inside_degree_celsius_constraint)
            else:
                # Inside temperature is a function of heating/cooling and
                # outside temperature. Alpha, beta and gamma are parameters
                # derived from the R and C values of the building.
                previous_building_internal_temperature_in_celsius_degrees = \
                    building_internal_temperature_in_celsius_degrees[
                        energy_management_system_time_interval_per_day - 1, number_of_building]
                chiller_coefficient_of_performance = \
                    self.building_assets[number_of_building].chiller_coefficient_of_performance
                previous_cooling_active_power_in_kilowatts = \
                    cooling_active_power_in_kilowatts[
                        energy_management_system_time_interval_per_day - 1, number_of_building]
                heat_pump_coefficient_of_performance = \
                    self.building_assets[number_of_building].heat_pump_coefficient_of_performance
                previous_heating_active_power_in_kilowatts = \
                    heating_active_power_in_kilowatts[
                        energy_management_system_time_interval_per_day - 1, number_of_building]
                previous_ambient_temperature_in_degree_celsius = \
                    self.building_assets[number_of_building].ambient_temperature_in_degree_celsius[
                        energy_management_system_time_interval_per_day - 1]
                temperature_constraint = \
                    get_temperature_constraint_for_no_initial_time(
                        alpha=alpha, beta=beta, gamma=gamma,
                        previous_building_internal_temperature_in_celsius_degrees=
                        previous_building_internal_temperature_in_celsius_degrees,
                        chiller_coefficient_of_performance=chiller_coefficient_of_performance,
                        previous_cooling_active_power_in_kilowatts=previous_cooling_active_power_in_kilowatts,
                        heat_pump_coefficient_of_performance=heat_pump_coefficient_of_performance,
                        previous_heating_active_power_in_kilowatts=previous_heating_active_power_in_kilowatts,
                        previous_ambient_temperature_in_degree_celsius=
                        previous_ambient_temperature_in_degree_celsius)

                problem.add_constraint(
                    building_internal_temperature_in_celsius_degrees[
                        energy_management_system_time_interval_per_day,
                        number_of_building] == temperature_constraint)

    def add_linear_battery_model_constraints_to_the_problem(
            self, number_of_storage_assets: int, problem: pic.Problem,
            controllable_assets_active_power_in_kilowatts: float, number_of_buildings: int, asum: pic.Constant):

        # linear battery model constraints
        for number_of_storage_asset in range(number_of_storage_assets):
            battery_max_power_constraint_in_kilowatts = \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] \
                <= float(self.storage_assets[number_of_storage_asset].max_active_power_in_kilowatts[0])
            problem.add_constraint(battery_max_power_constraint_in_kilowatts)
            battery_min_power_constraint_in_kilowatts = \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] \
                >= float(self.storage_assets[number_of_storage_asset].min_active_power_in_kilowatts[0])
            problem.add_constraint(battery_min_power_constraint_in_kilowatts)
            # maximum energy constraint
            battery_max_energy_constraint_in_kilowatt_hour = \
                self.energy_management_system_time_series_resolution_in_hours * asum * \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] <= \
                float(self.storage_assets[number_of_storage_asset].max_active_power_in_kilowatts[0]) - \
                self.storage_assets[number_of_storage_asset].initial_energy_level_in_kilowatt_hour
            problem.add_constraint(battery_max_energy_constraint_in_kilowatt_hour)

            battery_min_energy_constraint_in_kilowatt_hour = \
                self.energy_management_system_time_series_resolution_in_hours * asum * \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] >= \
                float(self.storage_assets[number_of_storage_asset].min_energy_in_kilowatt_hour[0]) - \
                self.storage_assets[number_of_storage_asset].initial_energy_level_in_kilowatt_hour
            problem.add_constraint(battery_min_energy_constraint_in_kilowatt_hour)

            final_energy_constraint = \
                self.energy_management_system_time_series_resolution_in_hours * \
                asum[self.number_of_energy_management_system_time_intervals_per_day - 1, :] * \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] == \
                self.storage_assets[number_of_storage_asset].required_terminal_energy_level_in_kilowatt_hour - \
                self.storage_assets[number_of_storage_asset].initial_energy_level_in_kilowatt_hour
            problem.add_constraint(final_energy_constraint)

    def add_import_and_export_constraints_to_the_problem(
            self, problem: pic.Problem, controllable_assets_active_power_in_kilowatts: float,
            resampled_non_dispatchable_assets_active_power_in_kilowatts: float,
            active_power_imports_in_kilowatts: float,
            active_power_exports_in_kilowatts: float, max_active_power_demand_in_kilowatts: float):

        for number_of_energy_management_system_time_interval_per_day in range(0, 40):
            power_balance_constraint = sum(controllable_assets_active_power_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day, :]) + \
                                       resampled_non_dispatchable_assets_active_power_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day] == \
                                       active_power_imports_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day] - \
                                       active_power_exports_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day]
            problem.add_constraint(power_balance_constraint)

            # maximum demand dummy variable constraint
            dummy_constraint = \
                max_active_power_demand_in_kilowatts >= active_power_imports_in_kilowatts[
                    number_of_energy_management_system_time_interval_per_day] - \
                active_power_exports_in_kilowatts[number_of_energy_management_system_time_interval_per_day]
            problem.add_constraint(dummy_constraint)

        # Blackout
        for number_of_energy_management_system_time_interval_per_day in range(40, 50):
            problem.add_constraint(controllable_assets_active_power_in_kilowatts[number_of_energy_management_system_time_interval_per_day] == 0)
            problem.add_constraint(active_power_imports_in_kilowatts[number_of_energy_management_system_time_interval_per_day] == 0)
            problem.add_constraint(active_power_exports_in_kilowatts[number_of_energy_management_system_time_interval_per_day] == 0)

            # # maximum demand dummy variable constraint
            # dummy_constraint = \
            #     max_active_power_demand_in_kilowatts >= active_power_imports_in_kilowatts[
            #         number_of_energy_management_system_time_interval_per_day] - \
            #     active_power_exports_in_kilowatts[number_of_energy_management_system_time_interval_per_day]
            # problem.add_constraint(dummy_constraint)

        for number_of_energy_management_system_time_interval_per_day in range(50, 96):
            power_balance_constraint = sum(controllable_assets_active_power_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day, :]) + \
                                       resampled_non_dispatchable_assets_active_power_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day] == \
                                       active_power_imports_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day] - \
                                       active_power_exports_in_kilowatts[
                                           number_of_energy_management_system_time_interval_per_day]
            problem.add_constraint(power_balance_constraint)

            # maximum demand dummy variable constraint
            dummy_constraint = \
                max_active_power_demand_in_kilowatts >= active_power_imports_in_kilowatts[
                    number_of_energy_management_system_time_interval_per_day] - \
                active_power_exports_in_kilowatts[number_of_energy_management_system_time_interval_per_day]
            problem.add_constraint(dummy_constraint)

    def add_frequency_response_constraints_to_the_problem(
            self, number_of_storage_assets: int, problem: pic.Problem, asum: pic.Constant,
            controllable_assets_active_power_in_kilowatts: float, number_of_buildings: int):

        if self.market.frequency_response_active is not None:
            frequency_response_window = self.market.frequency_response_active
            max_state_of_charge_for_frequency_response = self.market.max_frequency_response_state_of_charge
            min_state_of_charge_for_frequency_response = self.market.min_frequency_response_state_of_charge

            for energy_management_system_time_interval_per_day in range(
                    self.number_of_energy_management_system_time_intervals_per_day):
                if frequency_response_window:
                    self.get_final_energy_constraints(
                        number_of_storage_assets=number_of_storage_assets, problem=problem, asum=asum,
                        energy_management_system_time_interval_per_day=energy_management_system_time_interval_per_day,
                        controllable_assets_active_power_in_kilowatts=controllable_assets_active_power_in_kilowatts,
                        number_of_buildings=number_of_buildings,
                        max_state_of_charge_for_frequency_response=max_state_of_charge_for_frequency_response,
                        min_state_of_charge_for_frequency_response=min_state_of_charge_for_frequency_response)

    def get_final_energy_constraints(
            self, number_of_storage_assets: int, problem: pic.Problem, asum: pic.Constant,
            energy_management_system_time_interval_per_day, controllable_assets_active_power_in_kilowatts: float,
            number_of_buildings: int, max_state_of_charge_for_frequency_response: float,
            min_state_of_charge_for_frequency_response: float):

        for number_of_storage_asset in range(number_of_storage_assets):
            # final energy constraint
            final_energy_constraint_1 = \
                self.energy_management_system_time_series_resolution_in_hours * \
                asum[energy_management_system_time_interval_per_day, :] * \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] <= \
                (max_state_of_charge_for_frequency_response *
                 self.storage_assets[number_of_storage_asset].max_energy_in_kilowatt_hour) - \
                self.storage_assets[number_of_storage_asset].initial_energy_level_in_kilowatt_hour
            problem.add_constraint(final_energy_constraint_1)

            final_energy_constraint_2 = \
                self.energy_management_system_time_series_resolution_in_hours * \
                asum[energy_management_system_time_interval_per_day, :] * \
                controllable_assets_active_power_in_kilowatts[:, number_of_buildings + number_of_storage_asset] >= \
                (min_state_of_charge_for_frequency_response *
                 self.storage_assets[number_of_storage_asset].max_energy_in_kilowatt_hour) - \
                self.storage_assets[number_of_storage_asset].initial_energy_level_in_kilowatt_hour
            problem.add_constraint(final_energy_constraint_2)
