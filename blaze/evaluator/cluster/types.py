""" Implement common types for the cluster package """

from typing import Callable, TypeVar

T = TypeVar("T")
DistanceFunc = Callable[[T, T], float]
