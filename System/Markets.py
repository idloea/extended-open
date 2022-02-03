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

#import modules
import copy
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import numpy as np
import picos as pic
import matplotlib.pyplot as plt
from datetime import date, timedelta
import os
import requests
from scipy.interpolate import interp1d
from sklearn.cluster import KMeans

__version__ = "1.0.0"

#Market Base Class
class Market:
    """
    A market class to handle prices and other market associated parameters.

    Parameters
    ----------
    bus_id : int
        id number of the bus in the network
    prices_export : numpy.ndarray
        price paid for exports (£/kWh)
    prices_import : numpy.ndarray
        price charged for imports (£/kWh)
    demand_charge : float
        charge for the maximum demand over the time series (£/kWh)
    Pmax : float
        maximum import power over the time series (kW)
    Pmin : float
        minimum import over the time series (kW)
    dt_market : float
        time interval duration (minutes)
    T_market : int
        number of time intervals
    FR_window : int 
        binary value over time series to indicate when frequency response has 
        been offered (0,1)
    FR_capacity : float
        capacity of frequency response offered (kW)
    FR_SOC_max : float
        max SOC at which frequency response can still be fulfilled if needed
    FR_SOC_min : float
        min SOC at which frequency response can still be fulfilled if needed
    FR_price : float
        price per kW capacity per hour avaiable (£/kW.h)
    

    Returns
    -------
    Market


    """
     
    def __init__(self, bus_id, prices_export, prices_import, demand_charge,
                 Pmax, Pmin, dt_market, T_market, FR_window = None,
                 FR_capacity = None, FR_SOC_max = 0.6,
                 FR_SOC_min = 0.4, FR_price = 5/1000, stochastic_date=None, 
                 daily_connection_charge = 0.13):
        #id number of the bus in the network
        self.bus_id = bus_id 
        #price paid for exports (£/kWh)
        self.prices_export = prices_export 
        #price charged for imports (£/kWh)
        self.prices_import = prices_import 
        #charge for the maximum demand over the time series (£/kWh)
        self.demand_charge = demand_charge 
        #maximum import power over the time series (kW)
        self.Pmax = Pmax 
        #minimum import over the time series (kW)
        self.Pmin = Pmin 
        #time interval duration
        self.dt_market = dt_market 
        #number of time intervals
        self.T_market = T_market
        #time window during which frequency response has been offered
        self.FR_window = FR_window
        #capacity of frequency response offered (kW)
        self.FR_capacity = FR_capacity
        #max SOC at which frequency response can still be fulfilled if needed
        self.FR_SOC_max = FR_SOC_max
        #min SOC at which frequency response can still be fulfilled if needed
        self.FR_SOC_min = FR_SOC_min
        #price per kW capacity per hour avaiable (£/kW.h)
        self.FR_price = FR_price
        #cost from energy supplier for daily connection to the grid
        self.daily_connection_charge = daily_connection_charge
        #Total earnings from offering frequency response (initate as 0)
        self.FR_price_tot = 0
        
    
        
    def calculate_revenue(self, P_import_tot, dt):
        """
        Calculate revenue according to simulation results

        Parameters
        ----------
        P_import_tot : float
            Total import power to the site over the time series (kW)
        dt : float
            simulation time interval duration (minutes)
        c_deg_lin : float
            cost of battery degradation associated with each kWh throughput 
            (£/kWh)

        Returns
        -------
        revenue : float
            Total revenue generated during simulation

        """
        #convert import power to the market time-series
        P_import_market = np.zeros(self.T_market)
        for t_market in range(self.T_market):
            t_indexes = (t_market*self.dt_market/dt \
                         + np.arange(0,self.dt_market/dt)).astype(int)
            P_import_market[t_market] = np.mean(P_import_tot[t_indexes])
        #calcuate the revenue
        P_max_demand = np.max(P_import_market)
        P_import = np.maximum(P_import_market,0)
        P_export = np.maximum(-P_import_market,0)
        revenue = -self.demand_charge*P_max_demand+\
                  sum(-1*self.prices_import[t]*P_import[t]*self.dt_market+\
                  +self.prices_export[t]*P_export[t]*self.dt_market\
                                     for t in range(self.T_market))
        if self.FR_window is not None:
            FR_price_tot = self.FR_price*self.FR_capacity*\
            np.count_nonzero(self.FR_window)*self.dt_market
        else: FR_price_tot = 0
        revenue = float(revenue+FR_price_tot)
        return revenue
