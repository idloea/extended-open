#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPEN Markets module

A Market class defines an upstream market which the EnergySystem is connected
to. Attributes include the network location, prices of imports and exports
over the simulation time-series, the demand charge paid on the maximum demand
over the simulation time-series and import and export power limits. 

The market class has a method which calculates the total revenue associated
with a particular set of real and reactive power profiles over the simulation
time-series.

"""
from typing import List

import numpy as np
from abc import ABC, abstractmethod

from src.time_intervals import get_number_of_time_intervals_per_day


class Market(ABC):
    def __init__(self,
                 network_bus_id: int,
                 market_time_series_minute_resolution: float,
                 export_prices_in_pounds_per_kilowatt_hour: float,
                 peak_period_import_prices_in_pounds_per_kilowatt_hour: float,
                 peak_period_hours_per_day: int,
                 valley_period_import_prices_in_pounds_per_kilowatt_hour: float,
                 valley_period_hours_per_day: int,
                 max_demand_charge_in_pounds_per_kWh: float,
                 max_import_kilowatts: float,
                 max_export_kilowatts: float,
                 offered_kW_in_frequency_response: float,
                 max_frequency_response_state_of_charge: float,
                 min_frequency_response_state_of_charge: float,
                 frequency_response_price_in_pounds_per_kilowatt_hour: float):

        self.network_bus_id = network_bus_id
        self.market_time_series_minute_resolution = market_time_series_minute_resolution
        self.number_of_market_time_intervals = \
            get_number_of_time_intervals_per_day(self.market_time_series_minute_resolution)
        self.number_of_energy_management_system_time_intervals_per_day = self.number_of_market_time_intervals

        self.export_prices_in_pounds_per_kilowatt_hour = export_prices_in_pounds_per_kilowatt_hour
        self.export_price_time_series_in_pounds_per_kWh = self._get_export_prices_for_each_market_interval()

        self.peak_period_import_prices = peak_period_import_prices_in_pounds_per_kilowatt_hour
        self.peak_period_hours_per_day = peak_period_hours_per_day
        self.valley_period_import_prices = valley_period_import_prices_in_pounds_per_kilowatt_hour
        self.valley_period_hours_per_day = valley_period_hours_per_day
        self.max_demand_charge_in_pounds_per_kWh = max_demand_charge_in_pounds_per_kWh

        self.peak_import_prices_in_pounds_per_kWh = self._get_peak_period_import_prices()
        self.valley_import_prices_in_pounds_per_kWh = self._get_valley_period_import_prices()
        self.import_prices_in_pounds_per_kWh = self._get_prices_in_pounds_per_kilowatts()

        self.max_import_kilowatts = max_import_kilowatts * np.ones(self.number_of_market_time_intervals)
        self.max_export_kilowatts = max_export_kilowatts * np.ones(self.number_of_market_time_intervals)

        self.frequency_response_price_in_pounds_per_kilowatt_hour = offered_kW_in_frequency_response
        self.frequency_response_active = self._is_frequency_response_active()
        self.max_frequency_response_state_of_charge = max_frequency_response_state_of_charge
        self.min_frequency_response_state_of_charge = min_frequency_response_state_of_charge
        self.frequency_response_price_in_pounds_per_kWh = frequency_response_price_in_pounds_per_kilowatt_hour
        self.total_frequency_response_earnings = 0  # Initiate as 0

    def calculate_revenue(self, total_import_kW: float, simulation_time_interval_in_minutes: float) -> float:
        """
        Calculate revenue according to simulation results
        """
        self.average_imported_kilowatts = self._get_average_imported_kilowatts(
            total_import_kW=total_import_kW, simulation_time_interval_in_minutes=simulation_time_interval_in_minutes)

        imported_kilowatts = self._get_imported_kilowatts_from_the_market()
        exported_kilowatts = self._get_exported_kilowatts_to_the_market()

        max_imported_kilowatts = np.max(self.average_imported_kilowatts)

        revenue_between_import_and_export = self._get_revenue_between_import_and_export_kilowatts(
            imported_kilowatts=imported_kilowatts, exported_kilowatts=exported_kilowatts)
        revenue_between_import_and_export_sum = sum(revenue_between_import_and_export)

        max_imported_kilowatts_cost = self.max_demand_charge_in_pounds_per_kWh * max_imported_kilowatts
        revenue_without_frequency_response = revenue_between_import_and_export_sum - max_imported_kilowatts_cost

        total_frequency_response_revenue = self._get_total_frequency_response_revenue()

        return float(revenue_without_frequency_response + total_frequency_response_revenue)

    def _get_export_prices_for_each_market_interval(self) -> np.array:
        return self.export_prices_in_pounds_per_kilowatt_hour * np.ones(self.number_of_market_time_intervals)

    def _get_imported_kilowatts_from_the_market(self) -> np.array:
        imported_kilowatts = self.average_imported_kilowatts
        return np.maximum(imported_kilowatts, 0)

    def _get_exported_kilowatts_to_the_market(self) -> np.array:
        exported_kilowatts = -self.average_imported_kilowatts
        return np.maximum(exported_kilowatts, 0)

    def _get_average_imported_kilowatts(self, total_import_kW: float, simulation_time_interval_in_minutes: float):
        average_imported_kilowatts = np.zeros(self.number_of_market_time_intervals)
        market_time_intervals_range = range(self.number_of_market_time_intervals)
        for market_time_interval in market_time_intervals_range:
            time_indexes = (market_time_interval * self.market_time_series_minute_resolution / simulation_time_interval_in_minutes
                            + np.arange(0, self.market_time_series_minute_resolution /
                                        simulation_time_interval_in_minutes)).astype(int)
            average_imported_kilowatts[market_time_interval] = np.mean(total_import_kW[time_indexes])
        return average_imported_kilowatts

    def _get_revenue_between_import_and_export_kilowatts(self, imported_kilowatts: np.array,
                                                         exported_kilowatts) -> List:
        revenues = []
        for time_interval in range(self.number_of_market_time_intervals):
            import_revenue = self._get_import_revenue(time_interval=time_interval,
                                                      imported_kilowatts=imported_kilowatts)
            export_revenue = self._get_export_revenue(time_interval=time_interval,
                                                      exported_kilowatts=exported_kilowatts)
            revenue_difference = export_revenue - import_revenue
            revenues.append(revenue_difference)
        return revenues

    def _get_total_frequency_response_revenue(self):
        if self.frequency_response_active:
            total_frequency_response_revenue = self.frequency_response_price_in_pounds_per_kWh * \
                                               self.frequency_response_price_in_pounds_per_kilowatt_hour * \
                                               np.count_nonzero(self.frequency_response_active) * \
                                               self.market_time_series_minute_resolution
        else:
            total_frequency_response_revenue = 0
        return total_frequency_response_revenue

    def _get_import_revenue(self, time_interval: int, imported_kilowatts: np.array):
        return self.import_prices_in_pounds_per_kWh[time_interval] * imported_kilowatts[time_interval] * \
               self.market_time_series_minute_resolution

    def _get_export_revenue(self, time_interval: int, exported_kilowatts: np.array):
        return self.export_price_time_series_in_pounds_per_kWh[time_interval] * exported_kilowatts[time_interval] * \
               self.market_time_series_minute_resolution

    def _is_frequency_response_active(self):
        if self.frequency_response_price_in_pounds_per_kilowatt_hour > 0:
            frequency_response_active = True
        else:
            frequency_response_active = False
        return frequency_response_active

    def _get_peak_period_import_prices(self):
        peak_period_percentage_per_day = self.peak_period_hours_per_day / 24
        return self.peak_period_import_prices * np.ones(int(self.number_of_market_time_intervals *
                                                            peak_period_percentage_per_day))

    def _get_valley_period_import_prices(self):
        valley_period_percentage_per_day = self.valley_period_hours_per_day / 24
        return self.valley_period_import_prices * np.ones(int(self.number_of_market_time_intervals *
                                                              valley_period_percentage_per_day))

    def _get_prices_in_pounds_per_kilowatts(self):
        return np.hstack((self.peak_import_prices_in_pounds_per_kWh, self.valley_import_prices_in_pounds_per_kWh))
