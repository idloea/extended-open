"""
OPEN Asset module

Asset objects define distributed energy resources (DERs) and loads.
Attributes include network location, phase connection and real and reactive
output power profiles over the simulation time-series. 
Flexible Asset classes have an update control method, which is called by
EnergySystem simulation methods with control references to update the output
power profiles and state variables. The update control method also implements
constraints which limit the implementation of references. 
OPEN includes the following Asset subclasses: NondispatchableAsset for
uncontrollable loads and generation sources, StorageAsset for storage systems
and BuildingAsset for buildings with flexible heating, ventilation and air
conditioning (HVAC).
"""

from typing import List

import numpy as np


__version__ = "1.1.0"

from src.time_intervals import get_number_of_time_intervals_per_day


class Asset:
    """ An energy resource located at a particular bus in the network """
    def __init__(self,
                 bus_id: float,
                 simulation_time_series_hour_resolution: float,
                 phases: List = [0, 1, 2]):

        self.bus_id = bus_id
        self.simulation_time_series_hour_resolution = simulation_time_series_hour_resolution
        self.phases = np.array(phases)

        self.number_of_time_intervals_per_day = get_number_of_time_intervals_per_day(
            time_series_resolution_in_hours=self.simulation_time_series_hour_resolution)


class BuildingAsset(Asset):
    """ A building asset (use for flexibility from building HVAC) """
    def __init__(self,
                 max_inside_degree_celsius: float,
                 min_inside_degree_celsius: float,
                 max_consumed_electric_heating_kilowatts: float,
                 max_consumed_electric_cooling_kilowatts: float,
                 initial_inside_degree_celsius: float,
                 building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius: float,
                 building_thermal_resistance_in_degree_celsius_per_kilowatts: float,
                 heat_pump_coefficient_of_performance: float,
                 chiller_coefficient_of_performance: float,
                 ambient_temperature_in_degree_celsius: np.ndarray,
                 bus_id: int,
                 simulation_time_series_hour_resolution: float,
                 energy_management_system_time_series_resolution_in_hours: float):

        Asset.__init__(self,
                       bus_id=bus_id,
                       simulation_time_series_hour_resolution=simulation_time_series_hour_resolution)
        self.max_inside_degree_celsius = max_inside_degree_celsius
        self.min_inside_degree_celsius = min_inside_degree_celsius
        self.max_consumed_electric_heating_kilowatts = max_consumed_electric_heating_kilowatts
        self.max_consumed_electric_cooling_kilowatts = max_consumed_electric_cooling_kilowatts
        self.energy_management_system_time_series_hour_resolution = \
            energy_management_system_time_series_resolution_in_hours
        self.initial_inside_degree_celsius = initial_inside_degree_celsius
        self.building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = \
            building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius
        self.building_thermal_resistance_in_degree_celsius_per_kilowatts = \
            building_thermal_resistance_in_degree_celsius_per_kilowatts
        self.heat_pump_coefficient_of_performance = heat_pump_coefficient_of_performance
        self.chiller_coefficient_of_performance = chiller_coefficient_of_performance
        self.energy_management_system_time_series_hour_resolution = \
            energy_management_system_time_series_resolution_in_hours
        self.number_of_energy_management_system_time_intervals_per_day = \
            int(24 / self.energy_management_system_time_series_hour_resolution)
        self.number_of_time_intervals_per_day = int(24 / self.simulation_time_series_hour_resolution)
        self.alpha = (1 - (energy_management_system_time_series_resolution_in_hours /
                           (building_thermal_resistance_in_degree_celsius_per_kilowatts *
                            building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius)))
        self.beta = (energy_management_system_time_series_resolution_in_hours /
                     building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius)
        self.gamma = energy_management_system_time_series_resolution_in_hours / \
                     (building_thermal_resistance_in_degree_celsius_per_kilowatts *
                      building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius)
        self.active_power_in_kilowatts = np.zeros(self.number_of_time_intervals_per_day)   # input powers over the time series (kW)
        self.reactive_power = np.zeros(self.number_of_time_intervals_per_day)   # reactive powers over the time series (kW)
        self.max_inside_degree_celsius = max_inside_degree_celsius * np.ones(
            self.number_of_energy_management_system_time_intervals_per_day)
        self.min_inside_degree_celsius = min_inside_degree_celsius * np.ones(
            self.number_of_energy_management_system_time_intervals_per_day)
        self.ambient_temperature_in_degree_celsius = ambient_temperature_in_degree_celsius * np.ones(
            self.number_of_energy_management_system_time_intervals_per_day)  # TODO adapt the code to be able to handle cases from UK and Pamplona

    def update_control(self, active_power):
        """
        Update the power consumed by the HVAC at time interval t

        Parameters
        ----------
        active_power : numpy.ndarray
            input powers over the time series (kW)
        """
        self.active_power_in_kilowatts = active_power


# NEEDED FOR OXEMF EV CASE
class StorageAsset(Asset):
    """ A storage asset (use for batteries, EVs etc.) """

    def __init__(self,
                 max_energy_in_kilowatt_hour: np.ndarray,
                 min_energy_in_kilowatt_hour: np.ndarray,
                 max_active_power_in_kilowatts: np.ndarray,
                 min_active_power_in_kilowatts: np.ndarray,
                 initial_energy_level_in_kilowatt_hour: float,
                 required_terminal_energy_level_in_kilowatt_hour: float,
                 bus_id: int,
                 simulation_time_series_hour_resolution: float,
                 number_of_time_intervals_per_day: int,
                 energy_management_system_time_series_resolution_in_seconds: float,
                 number_of_energy_management_system_time_intervals_per_day: int,
                 absolute_active_power_in_kilowatts=None,
                 battery_degradation_ratio_in_euros_per_kilowatt_hour=None,
                 charging_efficiency=1,
                 charging_efficiency_for_the_optimizer=1):
        Asset.__init__(self, bus_id, simulation_time_series_hour_resolution)
        self.max_energy_in_kilowatt_hour = max_energy_in_kilowatt_hour
        self.min_energy_in_kilowatt_hour = min_energy_in_kilowatt_hour
        self.max_active_power_in_kilowatts = max_active_power_in_kilowatts
        self.min_active_power_in_kilowatts = min_active_power_in_kilowatts
        if absolute_active_power_in_kilowatts is None:
            self.absolute_active_power_in_kilowatts = max(self.max_active_power_in_kilowatts)
        else:
            self.absolute_active_power_in_kilowatts = absolute_active_power_in_kilowatts
        self.initial_energy_level_in_kilowatt_hour = initial_energy_level_in_kilowatt_hour
        self.required_terminal_energy_level_in_kilowatt_hour = required_terminal_energy_level_in_kilowatt_hour
        self.energy_level_in_kilowatt_hour = \
            initial_energy_level_in_kilowatt_hour * np.ones(number_of_time_intervals_per_day + 1)
        self.energy_management_system_time_series_resolution_in_seconds = \
            energy_management_system_time_series_resolution_in_seconds
        self.number_of_energy_management_system_time_intervals_per_day = \
            number_of_energy_management_system_time_intervals_per_day
        self.active_power_in_kilowatts = np.zeros(number_of_time_intervals_per_day)
        self.reactive_power_in_kilovolt_ampere_reactive = np.zeros(number_of_time_intervals_per_day)
        self.battery_degradation_ratio_in_euros_per_kilowatt_hour = \
            battery_degradation_ratio_in_euros_per_kilowatt_hour or 0
        self.charging_efficiency = charging_efficiency * np.ones(100)
        self.charging_efficiency_for_the_optimizer = charging_efficiency_for_the_optimizer

    def update_control(self, active_power_in_kilowatts):
        """
        Update the storage system power and energy profile

        Parameters
        ----------
        active_power_in_kilowatts : float
            input powers over the time series (kW)

        """
        self.active_power_in_kilowatts = active_power_in_kilowatts
        self.energy_level_in_kilowatt_hour[0] = self.initial_energy_level_in_kilowatt_hour
        energy_management_system_time = self.simulation_time_series_hour_resolution / self.energy_management_system_time_series_resolution_in_seconds
        for t in range(self.number_of_time_intervals_per_day):
            P_ratio = int(100 * (abs(self.active_power_in_kilowatts[t] / self.absolute_active_power_in_kilowatts)))
            P_eff = self.charging_efficiency[P_ratio-1]
            if self.active_power_in_kilowatts[t] < 0:
                if self.energy_level_in_kilowatt_hour[t] <= self.min_energy_in_kilowatt_hour[int(t * energy_management_system_time)]:
                    self.energy_level_in_kilowatt_hour[t] = self.min_energy_in_kilowatt_hour[int(t * energy_management_system_time)]
                    self.active_power_in_kilowatts[t] = 0
                self.energy_level_in_kilowatt_hour[t + 1] = self.energy_level_in_kilowatt_hour[t] + (1 / P_eff) * self.active_power_in_kilowatts[t] * self.simulation_time_series_hour_resolution
            elif self.active_power_in_kilowatts[t] >= 0:
                if self.energy_level_in_kilowatt_hour[t] >= self.max_energy_in_kilowatt_hour[int(t * energy_management_system_time)]:
                    self.energy_level_in_kilowatt_hour[t] = self.max_energy_in_kilowatt_hour[int(t * energy_management_system_time)]
                    self.active_power_in_kilowatts[t] = 0
                self.energy_level_in_kilowatt_hour[t + 1] = self.energy_level_in_kilowatt_hour[t] + P_eff * self.active_power_in_kilowatts[t] * self.simulation_time_series_hour_resolution
# NEEDED FOR OXEMF EV CASE
    def update_control_t(self, Pnet_t, t):
        """
        Update the storage system power and energy at time interval t

        Parameters
        ----------
        Pnet_t : float
            input powers over the time series (kW)
        t : int
            time interval

        """
        self.active_power_in_kilowatts[t] = Pnet_t
        self.energy_level_in_kilowatt_hour[0] = self.initial_energy_level_in_kilowatt_hour
        t_ems = self.simulation_time_series_hour_resolution / self.energy_management_system_time_series_resolution_in_seconds
        P_ratio = int(100 * (abs(self.active_power_in_kilowatts[t] / self.absolute_active_power_in_kilowatts)))
        P_eff = self.eff[P_ratio-1]
        if self.active_power_in_kilowatts[t] < 0:
            if self.energy_level_in_kilowatt_hour[t] <= self.min_energy_in_kilowatt_hour[int(t * t_ems)]:
                self.energy_level_in_kilowatt_hour[t] = self.min_energy_in_kilowatt_hour[int(t * t_ems)]
                self.active_power_in_kilowatts[t] = 0
            self.energy_level_in_kilowatt_hour[t + 1] = self.energy_level_in_kilowatt_hour[t] + (1 / P_eff) * self.active_power_in_kilowatts[t] * self.simulation_time_series_hour_resolution
        elif self.active_power_in_kilowatts[t] >= 0:
            if self.energy_level_in_kilowatt_hour[t] >= self.max_energy_in_kilowatt_hour[int(t * t_ems)]:
                self.energy_level_in_kilowatt_hour[t] = self.max_energy_in_kilowatt_hour[int(t * t_ems)]
                self.active_power_in_kilowatts[t] = 0
            self.energy_level_in_kilowatt_hour[t + 1] = self.energy_level_in_kilowatt_hour[t] + P_eff * self.active_power_in_kilowatts[t] * self.simulation_time_series_hour_resolution


class NonDispatchableAsset(Asset):
    """ A 3 phase nondispatchable asset class (use for inflexible loads,
    PVsources etc)"""

    def __init__(self,
                 simulation_time_series_hour_resolution: float,
                 bus_id: int,
                 active_power_in_kilowatts: np.ndarray,
                 reactive_power_in_kilovolt_ampere_reactive: np.ndarray,
                 phases: List = [0, 1, 2],
                 active_power_pred=None,
                 reactive_power_pred=None):

        self.simulation_time_series_hour_resolution = simulation_time_series_hour_resolution

        Asset.__init__(self,
                       bus_id=bus_id,
                       simulation_time_series_hour_resolution=simulation_time_series_hour_resolution,
                       phases=phases)

        self.active_power_in_kilowatts = active_power_in_kilowatts
        self.reactive_power = reactive_power_in_kilovolt_ampere_reactive

        self.active_power_pred = self._get_active_power_pred(active_power_pred=active_power_pred)
        self.reactive_power_pred = self._get_reactive_power_pred(reactive_power_pred=reactive_power_pred)

    def _get_active_power_pred(self, active_power_pred):
        if active_power_pred is not None:
            self.active_power_pred = active_power_pred
        else:
            self.active_power_pred = self.active_power_in_kilowatts
        return self.active_power_pred

    def _get_reactive_power_pred(self, reactive_power_pred):
        if reactive_power_pred is not None:
            self.reactive_power_pred = reactive_power_pred
        else:
            self.reactive_power_pred = self.reactive_power
        return self.reactive_power_pred

# =============================================================================
# Below 3ph assets to be removed in V 0.1.0
# =============================================================================
# Requires all calls of 3ph assets in other system files to have their names
# changed


class Asset_3ph(Asset):
    """
    An energy resource located at a particular bus in the 3 phase network

    Parameters
    ----------
    bus_id : float
        id number of the bus in the network
    phases : list
        [0, 1, 2] indicates 3 phase connection
        Wye: [0, 1] indicates an a,b connection
        Delta: [0] indicates a-b, [1] b-c, [2] c-a
    simulation_time_series_hour_resolution : float
        time interval duration
    number_of_time_intervals_per_day : int
        number of time intervals

    Returns
    -------
    Asset


    """
    def __init__(self, bus_id, phases, simulation_time_series_hour_resolution):
        Asset.__init__(self,
                       bus_id=bus_id,
                       simulation_time_series_hour_resolution=simulation_time_series_hour_resolution)
        self.phases = np.array(phases)


class StorageAsset_3ph(Asset_3ph):
    """
    An 3 phase storage asset (use for batteries, EVs etc.)

    Parameters
    ----------
    Emax : numpy.ndarray
        maximum energy levels over the time series (kWh)
    Emin : numpy.ndarray
        minimum energy levels over the time series (kWh)
    Pmax : numpy.ndarray
        maximum input powers over the time series (kW)
    Pmin : numpy.ndarray
        minimum input powers over the time series (kW)
    E0 : float
        initial energy level (kWh)
    ET : float
        required terminal energy level (kWh)
    bus_id : float
        id number of the bus in the network
    phases : list
        [0, 1, 2] indicates 3 phase connection
        Wye: [0, 1] indicates an a,b connection
        Delta: [0] indicates a-b, [1] b-c, [2] c-a
    simulation_time_series_hour_resolution : float
        time interval duration (s)
    number_of_time_intervals_per_day : int
        number of time intervals
    dt_ems : float
        time interval duration (energy management system time horizon) (s)
    T_ems : int
        number of time intervals (energy management system time horizon)
    phases : list, optional, default [0,1,2]
        [0, 1, 2] indicates 3 phase connection \
        Wye: [0, 1] indicates an a,b connection \
        Delta: [0] indicates a-b, [1] b-c, [2] c-a
    Pmax_abs : float
        max power level (kW)
    c_deg_lin : float
        battery degradation rate with energy throughput (£/kWh)
    eff : float, default 1
        charging efficiency (between 0 and 1).
    eff_opt : float, default 1
        charging efficiency to be used in optimiser (between 0 and 1).



    Returns
    -------
    Asset


    """
    def __init__(self, Emax, Emin, Pmax, Pmin, E0, ET, bus_id, phases, simulation_time_series_hour_resolution,
                 dt_ems, T_ems, Pmax_abs=None, c_deg_lin=None, eff=1,
                 eff_opt=1):
        Asset_3ph.__init__(self, bus_id, phases, simulation_time_series_hour_resolution)
        self.number_of_time_intervals_per_day = get_number_of_time_intervals_per_day(
            time_series_resolution_in_hours=self.simulation_time_series_hour_resolution)
        self.Emax = Emax
        self.Emin = Emin
        self.Pmax = Pmax
        self.Pmin = Pmin
        if Pmax_abs is None:
            self.Pmax_abs = max(self.Pmax)
        else:
            self.Pmax_abs = Pmax_abs
        self.E0 = E0
        self.ET = ET
        self.E = E0*np.ones(self.number_of_time_intervals_per_day + 1)
        self.dt_ems = dt_ems
        self.T_ems = T_ems
        self.Pnet = np.zeros(self.number_of_time_intervals_per_day)
        self.Qnet = np.zeros(self.number_of_time_intervals_per_day)
        self.c_deg_lin = c_deg_lin or 0
        self.eff = eff*np.ones(100)
        self.eff_opt = eff_opt

    def update_control(self, Pnet):
        """
        Update the storage system power and energy profile

        Parameters
        ----------
        Pnet : numpy.ndarray
            input powers over the time series (kW)

        """
        self.Pnet = Pnet
        self.E[0] = self.E0
        t_ems = self.simulation_time_series_hour_resolution / self.dt_ems
        for t in range(self.number_of_time_intervals_per_day):
            P_ratio = int(100*(abs(self.Pnet[t]/self.Pmax_abs)))
            P_eff = self.eff[P_ratio-1]
            if self.Pnet[t] < 0:
                if self.E[t] <= self.Emin[int(t*t_ems)]:
                    self.E[t] = self.Emin[int(t*t_ems)]
                    self.Pnet[t] = 0
                self.E[t+1] = self.E[t] + (1/P_eff)*self.Pnet[t]*self.simulation_time_series_hour_resolution
            elif self.Pnet[t] >= 0:
                if self.E[t] >= self.Emax[t]:
                    self.E[t] = self.Emax[t]
                    self.Pnet[t] = 0
                self.E[t+1] = self.E[t] + P_eff*self.Pnet[t]*self.simulation_time_series_hour_resolution

    def update_control_t(self, Pnet_t, t):
        """
        Update the storage system power and energy at time interval t

        Parameters
        ----------
        Pnet_t : numpy.ndarray
            input powers over the time series (kW)
        t : int
            time interval

        """
        self.Pnet[t] = Pnet_t
        self.E[0] = self.E0
        t_ems = self.simulation_time_series_hour_resolution / self.dt_ems
        P_ratio = int(100*(abs(self.Pnet[t]/self.Pmax_abs)))
        P_eff = self.eff[P_ratio-1]
        if self.Pnet[t] < 0:
            if self.E[t] <= self.Emin[int(t*t_ems)]:
                self.E[t] = self.Emin[int(t*t_ems)]
                self.Pnet[t] = 0
            self.E[t+1] = self.E[t] + (1/P_eff)*self.Pnet[t]*self.simulation_time_series_hour_resolution
        elif self.Pnet[t] >= 0:
            if self.E[t] >= self.Emax[int(t*t_ems)]:
                self.E[t] = self.Emax[int(t*t_ems)]
                self.Pnet[t] = 0
            self.E[t+1] = self.E[t] + P_eff*self.Pnet[t]*self.simulation_time_series_hour_resolution


class NondispatchableAsset_3ph(Asset_3ph):
    """
    A 3 phase nondispatchable asset class (use for inflexible loads,
    PVsources etc)

    Parameters
    ----------
    Pnet : float
        uncontrolled real input powers over the time series
    Qnet : float
        uncontrolled reactive input powers over the time series (kVar)
    bus_id : float
        id number of the bus in the network
    phases : list
        [0, 1, 2] indicates 3 phase connection
        Wye: [0, 1] indicates an a,b connection
        Delta: [0] indicates a-b, [1] b-c, [2] c-a
    simulation_time_series_hour_resolution : float
        time interval duration
    number_of_time_intervals_per_day : int
        number of time intervals
    Pnet_pred : float
        predicted real input powers over the time series (kW)
    Qnet_pred : float
        predicted reactive input powers over the time series (kVar)

    Returns
    -------
    Asset


    """

    def __init__(self, Pnet, Qnet, bus_id, phases, simulation_time_series_hour_resolution, Pnet_pred=None,
                 Qnet_pred=None):
        Asset_3ph.__init__(self, bus_id, phases, simulation_time_series_hour_resolution)
        self.Pnet = Pnet
        self.Qnet = Qnet
        if Pnet_pred is not None:
            self.Pnet_pred = Pnet_pred
        else:
            self.Pnet_pred = Pnet
        if Qnet_pred is not None:
            self.Qnet_pred = Qnet_pred
        else:
            self.Qnet_pred = Qnet
