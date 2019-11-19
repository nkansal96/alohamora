""" Implements distance functions for the """
import math
from typing import List

from blaze.config.environment import EnvironmentConfig

from .types import DistanceFunc


def linear_distance(a: float, b: float) -> float:
    """ Returns the absolute difference between a and b """
    return abs(a - b)


def euclidian_distance(a: List[float], b: List[float]) -> float:
    """ Returns the euclidian distance between two N-dimensional points """
    return math.sqrt(sum((x - y) ** 2 for (x, y) in zip(a, b)))


def create_apted_distance_function(port: int) -> DistanceFunc:
    """ Creates a distance function with a connection to the tree_diff server """
    # TODO: implement this
    def apted_distance(a: EnvironmentConfig, b: EnvironmentConfig) -> float:
        return 0.0

    return apted_distance
