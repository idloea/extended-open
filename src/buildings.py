from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Building(ABC):
    """Base class for the buildings"""
    hvac_percentage_of_electric_load: float = 0.0


@dataclass
class Hospital(Building):
    hvac_percentage_of_electric_load: float = 0.4


@dataclass
class Hotel(Building):
    hvac_percentage_of_electric_load: float = 0.4


@dataclass
class Office(Building):
    hvac_percentage_of_electric_load: float = 0.6
