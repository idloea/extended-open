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
                 export_prices_in_pounds_per_kWh: np.ndarray,
                 import_prices_in_pounds_per_kWh: np.ndarray,
                 max_demand_charge_in_pounds_per_kWh: float,
                 max_import_kW: float, min_import_kW: float,
                 minutes_market_interval: float,
                 number_of_market_time_intervals: int,
                 frequency_response_active: bool = False,
                 offered_kW_in_frequency_response: float = None,
                 max_frequency_response_state_of_charge: float = 0.6,
                 min_frequency_response_state_of_charge=0.4,
                 frequency_response_price_in_pounds_per_kWh=5 / 1000,
                 daily_connection_charge=0.13):
        self.network_bus_id = network_bus_id
        self.export_prices_in_pounds_per_kWh = export_prices_in_pounds_per_kWh
        self.import_prices_in_pounds_per_kWh = import_prices_in_pounds_per_kWh
        self.max_demand_charge_in_pounds_per_kWh = max_demand_charge_in_pounds_per_kWh
        self.max_import_kW = max_import_kW
        self.min_import_kW = min_import_kW
        self.minutes_market_interval = minutes_market_interval
        self.number_of_market_time_intervals = number_of_market_time_intervals
        self.frequency_response_active = frequency_response_active
        self.offered_kW_in_frequency_response = offered_kW_in_frequency_response
        self.max_frequency_response_state_of_charge = max_frequency_response_state_of_charge
        self.min_frequency_response_state_of_charge = min_frequency_response_state_of_charge
        self.frequency_response_price_in_pounds_per_kWh = frequency_response_price_in_pounds_per_kWh
        self.daily_connection_charge = daily_connection_charge
        self.total_frequency_response_earnings = 0  # Initiate as 0

    def calculate_revenue(self, total_import_kW: float, simulation_time_interval_in_minutes: float) -> float:
        """
        Calculate revenue according to simulation results
        """
        # convert import power to the market time-series
        import_market_kW_time_series = np.zeros(self.number_of_market_time_intervals)
        for time_interval in range(self.number_of_market_time_intervals):
            t_indexes = (time_interval * self.minutes_market_interval / simulation_time_interval_in_minutes +
                         np.arange(0, self.minutes_market_interval / simulation_time_interval_in_minutes)).astype(int)
            import_market_kW_time_series[time_interval] = np.mean(total_import_kW[t_indexes])
        # calculate the revenue
        import_kW = np.maximum(import_market_kW_time_series, 0)
        export_kW = np.maximum(-import_market_kW_time_series, 0)
        max_kW_demand = np.max(import_market_kW_time_series)

        export_import_revenues = []
        for time_interval in range(self.number_of_market_time_intervals):
            import_revenue = self.import_prices_in_pounds_per_kWh[time_interval] * import_kW[time_interval] *\
                             self.minutes_market_interval
            export_revenue = self.export_prices_in_pounds_per_kWh[time_interval] * export_kW[time_interval] *\
                             self.minutes_market_interval
            export_import_revenue = export_revenue - import_revenue
            export_import_revenues.append(export_import_revenue)

        export_import_revenue_sum = sum(export_import_revenues)
        max_demand_cost = self.max_demand_charge_in_pounds_per_kWh * max_kW_demand
        revenue_without_frequency_response = export_import_revenue_sum - max_demand_cost

        if self.frequency_response_active:
            total_frequency_response_revenue = self.frequency_response_price_in_pounds_per_kWh * \
                                                self.offered_kW_in_frequency_response * \
                                                np.count_nonzero(self.frequency_response_active) *\
                                                self.minutes_market_interval
        else:
            total_frequency_response_revenue = 0

        return float(revenue_without_frequency_response + total_frequency_response_revenue)
