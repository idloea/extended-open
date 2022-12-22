from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Building(ABC):
    """Base class for the buildings"""
    pass


@dataclass
class Hospital(Building):
    hvac_percentage_of_electric_load = 40


@dataclass
class Hotel(Building):
    hvac_percentage_of_electric_load = 40


@dataclass
class Office(Building):
    hvac_percentage_of_electric_load = 60
