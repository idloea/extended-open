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
from typing import List, Union
import numpy as np
from abc import ABC, abstractmethod

from src.read import get_specific_import_price
from src.time_intervals import get_number_of_time_intervals_per_day


class Market(ABC):
    def __init__(self,
                 network_bus_id: int,
                 market_time_series_resolution_in_hours: float,
                 export_prices_in_euros_per_kilowatt_hour: float,
                 import_periods: dict,
                 max_demand_charge_in_euros_per_kilowatt_hour: float,
                 max_import_kilowatts: float,
                 max_export_kilowatts: float,
                 offered_kilowatt_in_frequency_response: float,
                 max_frequency_response_state_of_charge: float,
                 min_frequency_response_state_of_charge: float,
                 frequency_response_price_in_euros_per_kilowatt_hour: float):
        self.network_bus_id = network_bus_id
        self.market_time_series_resolution_in_minutes = market_time_series_resolution_in_hours
        self.number_of_market_time_intervals_per_day = \
            get_number_of_time_intervals_per_day(self.market_time_series_resolution_in_minutes)
        self.number_of_energy_management_system_time_intervals_per_day = self.number_of_market_time_intervals_per_day

        self.export_prices_in_euros_per_kilowatt_hour = export_prices_in_euros_per_kilowatt_hour
        self.export_price_time_series_in_euros_per_kWh = self._get_export_prices_for_each_market_interval()

        self.import_periods = import_periods

        self.max_demand_charge_in_euros_per_kWh = max_demand_charge_in_euros_per_kilowatt_hour

        self.import_prices_in_euros_per_kilowatt_hour = self.get_import_costs_in_euros_per_day_and_period()

        self.max_import_kilowatts = max_import_kilowatts * np.ones(self.number_of_market_time_intervals_per_day)
        self.max_export_kilowatts = max_export_kilowatts * np.ones(self.number_of_market_time_intervals_per_day)

        self.offered_kilowatt_in_frequency_response = offered_kilowatt_in_frequency_response
        self.frequency_response_active = self._is_frequency_response_active()
        self.max_frequency_response_state_of_charge = max_frequency_response_state_of_charge
        self.min_frequency_response_state_of_charge = min_frequency_response_state_of_charge
        self.frequency_response_price_in_euros_per_kWh = frequency_response_price_in_euros_per_kilowatt_hour
        self.total_frequency_response_earnings = 0  # Initiate as 0

    def calculate_revenue(self, total_import_in_kilowatts: float, simulation_time_interval_in_minutes: float) -> float:
        """
        Calculate revenue according to simulation results
        """
        self.average_imported_kilowatts = self._get_average_imported_kilowatts(
            total_imports_in_kilowatts=total_import_in_kilowatts,
            simulation_time_interval_in_minutes=simulation_time_interval_in_minutes)

        imported_kilowatts = self._get_imported_kilowatts_from_the_market()
        exported_kilowatts = self._get_exported_kilowatts_to_the_market()

        max_imported_kilowatts = np.max(self.average_imported_kilowatts)

        revenue_between_import_and_export = self._get_revenue_between_import_and_export_kilowatts(
            imported_kilowatts=imported_kilowatts, exported_kilowatts=exported_kilowatts)
        revenue_between_import_and_export_sum = sum(revenue_between_import_and_export)

        max_imported_kilowatts_cost = self.max_demand_charge_in_euros_per_kWh * max_imported_kilowatts
        revenue_without_frequency_response = revenue_between_import_and_export_sum - max_imported_kilowatts_cost

        total_frequency_response_revenue = self._get_total_frequency_response_revenue()

        return float(revenue_without_frequency_response + total_frequency_response_revenue)

    def _get_export_prices_for_each_market_interval(self) -> np.array:
        return self.export_prices_in_euros_per_kilowatt_hour * np.ones(self.number_of_market_time_intervals_per_day)

    def _get_imported_kilowatts_from_the_market(self) -> np.array:
        imported_kilowatts = self.average_imported_kilowatts
        return np.maximum(imported_kilowatts, 0)

    def _get_exported_kilowatts_to_the_market(self) -> np.array:
        exported_kilowatts = -self.average_imported_kilowatts
        return np.maximum(exported_kilowatts, 0)

    def _get_average_imported_kilowatts(self, total_imports_in_kilowatts: float,
                                        simulation_time_interval_in_minutes: float) -> np.array:
        average_imported_kilowatts = np.zeros(self.number_of_market_time_intervals_per_day)
        market_time_intervals_range = range(self.number_of_market_time_intervals_per_day)
        for market_time_interval in market_time_intervals_range:
            time_indexes = (
                    market_time_interval * self.market_time_series_resolution_in_minutes /
                    simulation_time_interval_in_minutes + np.arange(0, self.market_time_series_resolution_in_minutes /
                                                                    simulation_time_interval_in_minutes)).astype(int)
            average_imported_kilowatts[market_time_interval] = np.mean(total_imports_in_kilowatts[time_indexes])
        return average_imported_kilowatts

    def _get_revenue_between_import_and_export_kilowatts(self, imported_kilowatts: np.array,
                                                         exported_kilowatts: np.array) -> List:
        revenues = []
        for time_interval in range(self.number_of_market_time_intervals_per_day):
            import_revenue = self._get_import_revenue(time_interval=time_interval,
                                                      imported_kilowatts=imported_kilowatts)
            export_revenue = self._get_export_revenue(time_interval=time_interval,
                                                      exported_kilowatts=exported_kilowatts)
            revenue_difference = export_revenue - import_revenue
            revenues.append(revenue_difference)
        return revenues

    def _get_total_frequency_response_revenue(self):
        if self.frequency_response_active:
            total_frequency_response_revenue = self.frequency_response_price_in_euros_per_kWh * \
                                               self.offered_kilowatt_in_frequency_response * \
                                               np.count_nonzero(self.frequency_response_active) * \
                                               self.market_time_series_resolution_in_minutes
        else:
            total_frequency_response_revenue = 0
        return total_frequency_response_revenue

    def _get_import_revenue(self, time_interval: int, imported_kilowatts: np.array):
        return self.import_prices_in_euros_per_kilowatt_hour[time_interval] * imported_kilowatts[time_interval] * \
               self.market_time_series_resolution_in_minutes

    def _get_export_revenue(self, time_interval: int, exported_kilowatts: np.array):
        return self.export_price_time_series_in_euros_per_kWh[time_interval] * exported_kilowatts[time_interval] * \
               self.market_time_series_resolution_in_minutes

    def _is_frequency_response_active(self):
        if self.offered_kilowatt_in_frequency_response > 0:
            frequency_response_active = True
        else:
            frequency_response_active = False
        return frequency_response_active

    @abstractmethod
    def get_import_costs_in_euros_per_day_and_period(self) -> List:
        pass


class OPENMarket(Market):

    def get_import_costs_in_euros_per_day_and_period(self) -> List:
        import_period_cost_in_euros_per_day_list = []
        for import_period in self.import_periods:
            import_period_values = list(import_period.values())[0]
            import_period_duration_in_hours = import_period_values[0]
            import_period_percentage_per_day = import_period_duration_in_hours / 24
            number_of_market_intervals_for_import_period = \
                import_period_percentage_per_day * self.number_of_market_time_intervals_per_day
            period_price_in_euros_per_kilowatt_hour = import_period_values[1]
            period_price_in_euros_per_kilowatt_hour_array = \
                period_price_in_euros_per_kilowatt_hour * np.ones(int(number_of_market_intervals_for_import_period))
            import_period_cost_in_euros_per_day_list.append(period_price_in_euros_per_kilowatt_hour_array)
        return np.hstack(import_period_cost_in_euros_per_day_list)


class SpanishMarket(Market):
    def __init__(self, import_period_prices: dict, network_bus_id: int,
                 market_time_series_resolution_in_hours: float, export_prices_in_euros_per_kilowatt_hour: float,
                 import_periods: dict, max_demand_charge_in_euros_per_kilowatt_hour: float,
                 max_import_kilowatts: float, max_export_kilowatts: float,
                 offered_kilowatt_in_frequency_response: float, max_frequency_response_state_of_charge: float,
                 min_frequency_response_state_of_charge: float,
                 frequency_response_price_in_euros_per_kilowatt_hour: float):
        self.import_period_prices = import_period_prices

        super().__init__(network_bus_id, market_time_series_resolution_in_hours,
                         export_prices_in_euros_per_kilowatt_hour, import_periods,
                         max_demand_charge_in_euros_per_kilowatt_hour, max_import_kilowatts, max_export_kilowatts,
                         offered_kilowatt_in_frequency_response, max_frequency_response_state_of_charge,
                         min_frequency_response_state_of_charge, frequency_response_price_in_euros_per_kilowatt_hour)

    def get_import_costs_in_euros_per_day_and_period(self) -> List:
        hours_per_day = 24
        hour_array = np.ones(hours_per_day)
        import_period_price_per_hour_list = []
        for import_period, period_hours in self.import_periods.items():
            import_period_price = get_specific_import_price(import_period_prices=self.import_period_prices,
                                                            import_period=import_period)
            period_hours_on = np.zeros_like(hour_array, dtype=int)
            period_hours_on[period_hours] = hour_array[period_hours]
            specific_import_period_price_per_hour = import_period_price * period_hours_on
            import_period_price_per_hour_list.append(specific_import_period_price_per_hour)
        import_period_price_per_hour_list = sum(import_period_price_per_hour_list)

        import_period_price_per_resolution_list = []
        market_time_intervals_hour_ratio = self.number_of_market_time_intervals_per_day / 24
        for price in import_period_price_per_hour_list:
            import_period_price_per_resolution = np.ones(int(market_time_intervals_hour_ratio))
            import_period_price_per_resolution_list.append(import_period_price_per_resolution * price)

        return np.hstack(import_period_price_per_resolution_list)


def get_market(case_data: dict,
               network_bus_id: int,
               market_time_series_resolution_in_hours: float,
               export_prices_in_euros_per_kilowatt_hour: float,
               import_periods: Union[List[dict], dict],
               max_demand_charge_in_euros_per_kilowatt_hour: float,
               max_import_kilowatts: float,
               max_export_kilowatts: float,
               offered_kilowatt_in_frequency_response: float,
               max_frequency_response_state_of_charge: float,
               min_frequency_response_state_of_charge: float,
               frequency_response_price_in_euros_per_kilowatt_hour: float,
               import_period_prices: Union[dict, None]) -> Market:
    case_market = case_data["market"]
    if case_market == 'OPEN':
        market = OPENMarket(network_bus_id, market_time_series_resolution_in_hours,
                            export_prices_in_euros_per_kilowatt_hour, import_periods,
                            max_demand_charge_in_euros_per_kilowatt_hour, max_import_kilowatts, max_export_kilowatts,
                            offered_kilowatt_in_frequency_response, max_frequency_response_state_of_charge,
                            min_frequency_response_state_of_charge, frequency_response_price_in_euros_per_kilowatt_hour)
    elif case_market == 'Spanish':
        market = SpanishMarket(import_period_prices, network_bus_id, market_time_series_resolution_in_hours,
                               export_prices_in_euros_per_kilowatt_hour, import_periods,
                               max_demand_charge_in_euros_per_kilowatt_hour, max_import_kilowatts, max_export_kilowatts,
                               offered_kilowatt_in_frequency_response, max_frequency_response_state_of_charge,
                               min_frequency_response_state_of_charge,
                               frequency_response_price_in_euros_per_kilowatt_hour)
    else:
        raise ValueError(f'Incorrect data_strategy input. {case_market} is not available. ')
    return market
