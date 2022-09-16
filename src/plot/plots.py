from typing import List
import numpy as np
from matplotlib import pyplot as plt
from src.assets import BuildingAsset
from src.hvac import get_hvac_consumed_electric_active_power_in_kilowatts


def plot_demand_base_and_total_imported_power(simulation_time_series_resolution_in_hours: float,
                                              number_of_time_intervals_per_day: int,
                                              active_power_demand_base_in_kilowatts: np.ndarray,
                                              market_active_power_in_kilowatts: np.ndarray, case: str) -> None:
    hours = simulation_time_series_resolution_in_hours * np.arange(number_of_time_intervals_per_day)
    max_time = max(hours)
    plt.figure(num=None, figsize=(6, 3), dpi=80, facecolor='w', edgecolor='k')
    plt.plot(hours, active_power_demand_base_in_kilowatts, '--', label='Demand')
    plt.plot(hours, market_active_power_in_kilowatts, label='Imports')
    plt.suptitle('Base Demand vs Imports from the Network')
    subtitle = 'Case: ' + str(case)
    plt.title(subtitle)
    plt.ylabel('Power [kW]')
    plt.xlabel('Time [h]')
    plt.xlim(0, max_time)
    plt.xticks(np.arange(0, max_time, step=1))
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_ambient_temperature(energy_management_system_time_series_resolution_in_hours: float,
                             number_of_energy_management_time_intervals_per_day: int,
                             ambient_temperature_in_degree_celsius: np.ndarray,
                             case: str) -> None:
    plt.figure(num=None, figsize=(6, 2.5), dpi=80, facecolor='w', edgecolor='k')
    hours = energy_management_system_time_series_resolution_in_hours * \
            np.arange(number_of_energy_management_time_intervals_per_day)
    max_time = max(hours)
    plt.plot(hours, ambient_temperature_in_degree_celsius)
    plt.suptitle('Ambient Temperature')
    subtitle = 'Case: ' + str(case)
    plt.title(subtitle)
    plt.ylabel('Temperature [ºC]')
    plt.xlabel('Time [h]')
    plt.xlim(0, max_time)
    plt.xticks(np.arange(0, max_time, step=1))
    plt.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_building_internal_temperature(number_of_buildings: int,
                                       energy_management_system_time_series_resolution_in_hours: float,
                                       number_of_energy_management_time_intervals_per_day: int,
                                       building_assets: List[BuildingAsset]) -> None:
    plt.figure(num=None, figsize=(6, 2.5), dpi=80, facecolor='w', edgecolor='k')
    energy_management_system_hours = energy_management_system_time_series_resolution_in_hours * np.arange(
        number_of_energy_management_time_intervals_per_day)
    for number_of_building in range(number_of_buildings):
        plt.plot(energy_management_system_hours,
                 building_assets[number_of_building].building_internal_temperature_in_celsius_degrees,
                 color='C0', label='Temperature')
    plt.plot(energy_management_system_hours,
             building_assets[number_of_building].max_inside_degree_celsius *
             np.ones(number_of_energy_management_time_intervals_per_day), 'r:', linestyle=':', zorder=11,
             label='Limits')
    plt.plot(energy_management_system_hours,
             building_assets[number_of_building].min_inside_degree_celsius *
             np.ones(number_of_energy_management_time_intervals_per_day), 'r:', linestyle=':', zorder=11)
    plt.xticks([0, 8, 16, 23.75], ('00:00', '08:00', '16:00', '00:00'))
    plt.xlabel('Time (hh:mm)')
    plt.xlim(0, max(energy_management_system_hours))
    plt.ylabel('Temperature ($^{o}C$)')
    plt.xlabel('Time (hh:mm)')
    plt.grid(True, alpha=0.5)
    plt.legend(loc='center right')
    plt.grid(alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_hvac_consumed_active_power_in_kilowatts(number_of_buildings: int,
                                                 simulation_time_series_resolution_in_hours: float,
                                                 number_of_time_intervals_per_day: int,
                                                 energy_management_system_time_series_resolution_in_hours: float,
                                                 number_of_energy_management_time_intervals_per_day: int,
                                                 building_assets: List[BuildingAsset],
                                                 max_consumed_electric_heating_kilowatts: int or None,
                                                 max_consumed_electric_cooling_kilowatts: int or None) -> None:
    plt.figure(num=None, figsize=(6, 2.5), dpi=80, facecolor='w', edgecolor='k')
    hours = simulation_time_series_resolution_in_hours * np.arange(number_of_time_intervals_per_day)

    hvac_consumed_electric_active_power_in_kilowatts = \
        get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts=
                                                             max_consumed_electric_heating_kilowatts,
                                                             max_consumed_electric_cooling_kilowatts=
                                                             max_consumed_electric_cooling_kilowatts)

    hvac_consumed_electric_active_power_in_kilowatts_value = \
        list(hvac_consumed_electric_active_power_in_kilowatts.values())[0]
    label = list(hvac_consumed_electric_active_power_in_kilowatts.keys())[0]
    for number_of_building in range(number_of_buildings):
        plt.plot(hours, building_assets[number_of_building].active_power_in_kilowatts, color='C0', label=label,
                 zorder=10)

    energy_management_system_hours = energy_management_system_time_series_resolution_in_hours * np.arange(
        number_of_energy_management_time_intervals_per_day)
    plt.hlines(hvac_consumed_electric_active_power_in_kilowatts_value, 0, max(energy_management_system_hours),
               linestyle=':', label='Maximum', color='red', zorder=11, )
    plt.ylabel('Power (kW)')
    plt.grid(True, alpha=0.5)
    plt.xticks([0, 8, 16, 23.75], ('00:00', '08:00', '16:00', '00:00'))
    plt.xlabel('Time (hh:mm)')
    plt.xlim(0, max(energy_management_system_hours))
    plt.ylim(0, hvac_consumed_electric_active_power_in_kilowatts_value * 1.5)
    plt.grid(True, alpha=0.5)
    plt.legend(loc='upper right')
    plt.grid(alpha=0.5)
    plt.show()
