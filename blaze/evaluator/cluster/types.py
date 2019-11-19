""" Implement common types for the cluster package """

from typing import Callable, TypeVar

# pylint: disable=invalid-name
T = TypeVar("T")
DistanceFunc = Callable[[T, T], float]
