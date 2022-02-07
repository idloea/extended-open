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


class Market(ABC):
    """
    A market class to handle prices and other market associated parameters.

    Parameters
    ----------
   frequency_response_active : int
        binary value over time series to indicate when frequency response has 
        been offered (0,1)
    offered_kW_in_frequency_response : float
        capacity of frequency response offered (kW)
    max_frequency_response_state_of_charge : float
        max SOC at which frequency response can still be fulfilled if needed
    min_frequency_response_state_of_charge : float
        min SOC at which frequency response can still be fulfilled if needed
    frequency_response_price_in_pounds_per_kWh : float
        price per kW capacity per hour available (£/kW.h)

    """

    def __init__(self, network_bus_id: int,
                 number_of_EMS_time_intervals: int,
                 export_prices_in_pounds_per_kWh: int,
                 import_prices_in_pounds_per_kWh: np.ndarray,
                 max_demand_charge_in_pounds_per_kWh: float,
                 max_import_kW: float, min_import_kW: float,
                 minutes_market_interval: float,
                 number_of_market_time_intervals: int,
                 offered_kW_in_frequency_response: float,
                 max_frequency_response_state_of_charge: float,
                 min_frequency_response_state_of_charge: float,
                 frequency_response_price_in_pounds_per_kWh: float,
                 daily_connection_charge: float):

        self.network_bus_id = network_bus_id
        self.export_prices_in_pounds_per_kWh = export_prices_in_pounds_per_kWh * np.ones(number_of_EMS_time_intervals)
        self.import_prices_in_pounds_per_kWh = import_prices_in_pounds_per_kWh
        self.max_demand_charge_in_pounds_per_kWh = max_demand_charge_in_pounds_per_kWh
        self.max_import_kW = max_import_kW
        self.min_import_kW = min_import_kW
        self.market_interval_in_minutes = minutes_market_interval
        self.number_of_market_time_intervals = number_of_market_time_intervals
        self.offered_kW_in_frequency_response = offered_kW_in_frequency_response
        self.frequency_response_active = self._is_frequency_response_active()
        self.max_frequency_response_state_of_charge = max_frequency_response_state_of_charge
        self.min_frequency_response_state_of_charge = min_frequency_response_state_of_charge
        self.frequency_response_price_in_pounds_per_kWh = frequency_response_price_in_pounds_per_kWh
        self.daily_connection_charge = daily_connection_charge
        self.total_frequency_response_earnings = 0  # Initiate as 0

    def _calculate_revenue(self, total_import_kW: float, simulation_time_interval_in_minutes: float) -> float:
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
            time_indexes = (market_time_interval * self.market_interval_in_minutes / simulation_time_interval_in_minutes
                            + np.arange(0, self.market_interval_in_minutes /
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
                                               self.offered_kW_in_frequency_response * \
                                               np.count_nonzero(self.frequency_response_active) * \
                                               self.market_interval_in_minutes
        else:
            total_frequency_response_revenue = 0
        return total_frequency_response_revenue

    def _get_import_revenue(self, time_interval: int, imported_kilowatts: np.array):
        return self.import_prices_in_pounds_per_kWh[time_interval] * imported_kilowatts[time_interval] * \
               self.market_interval_in_minutes

    def _get_export_revenue(self, time_interval: int, exported_kilowatts: np.array):
        return self.export_prices_in_pounds_per_kWh[time_interval] * exported_kilowatts[time_interval] * \
               self.market_interval_in_minutes

    def _is_frequency_response_active(self):
        if self.offered_kW_in_frequency_response > 0:
            frequency_response_active = True
        else:
            frequency_response_active = False
        return frequency_response_active
