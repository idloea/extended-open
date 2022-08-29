from typing import List
import numpy as np
from matplotlib import pyplot as plt
from src.assets import BuildingAsset


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


def plot_building_internal_temperature(number_of_buildings: int,
                                       energy_management_system_time_series_resolution_in_hours: float,
                                       number_of_energy_management_time_intervals_per_day: int,
                                       building_assets: List[BuildingAsset]) -> None:
    plt.figure(num=None, figsize=(6, 2.5), dpi=80, facecolor='w', edgecolor='k')
    hours = energy_management_system_time_series_resolution_in_hours * np.arange(
        number_of_energy_management_time_intervals_per_day)
    for number_of_building in range(number_of_buildings):
        plt.plot(hours,
                 building_assets[number_of_building].building_internal_temperature_in_celsius_degrees,
                 color='C0', label='Temperature')
    plt.plot(hours,
             building_assets[number_of_building].max_inside_degree_celsius *
             np.ones(number_of_energy_management_time_intervals_per_day), 'r:', linestyle=':', zorder=11,
             label='Limits')
    plt.plot(hours,
             building_assets[number_of_building].min_inside_degree_celsius *
             np.ones(number_of_energy_management_time_intervals_per_day), 'r:', linestyle=':', zorder=11)
    plt.xticks([0, 8, 16, 23.75], ('00:00', '08:00', '16:00', '00:00'))
    plt.xlabel('Time (hh:mm)')
    plt.xlim(0, max(hours))
    plt.ylabel('Temperature ($^{o}C$)')
    plt.xlabel('Time (hh:mm)')
    plt.grid(True, alpha=0.5)
    plt.legend(loc='center right')
    plt.grid(alpha=0.5)
    plt.tight_layout()
    plt.show()
