""" Main clustering logic """
import abc
from typing import Generic, List

import numpy as np
from sklearn.cluster import affinity_propagation, dbscan

from .types import T, DistanceFunc


class _Cluster(abc.ABC, Generic[T]):
    """
    Implements a clustering framework that takes a list of elements and a distance function that returns the
    distance between any two objects in the list. This class provides common functionality for all clustering
    algorithms and defines a common interface.
    """

    def __init__(self, distance_func: DistanceFunc):
        """ Initialize the Cluster object with a distance function """
        self.distance_func = distance_func
        self._memo = {}

    def memoized_distance_func(self, x: List[T], i: int, j: int) -> float:
        """ Memoized calls to the distance function, assuming that distance(x, x) == 0"""
        if i == j:
            return 0
        if (i, j) in self._memo:
            return self._memo[(i, j)]
        if (j, i) in self._memo:
            return self._memo[(j, i)]
        self._memo[(i, j)] = self.distance_func(x[i], x[j])
        return self._memo[(i, j)]

    def get_distance_matrix(self, x: List[T]) -> np.array:
        """ Returns an NxN matrix precomputed with the pairwise distances between all objects in the list """
        return np.array([[self.memoized_distance_func(x, i, j) for j in range(len(x))] for i in range(len(x))])

    @abc.abstractmethod
    def cluster(self, x: List[T]) -> List[int]:
        """ Returns a list the same as as the input list with cluster labels corresponding to each element """


class DBSSCANCluster(_Cluster):
    """ Uses the DBSCAN algorithm to perform clustering. """

    def cluster(self, x: List[T]) -> List[int]:
        # NB(nkansal96): The selection of `eps` here is arbitrary and most likely wrong. Until this is fixed,
        #   you should use `AffinityCluster`
        _, mapping = dbscan(self.get_distance_matrix(x), eps=2, min_samples=0, metric="precomputed")
        return mapping


class AffinityCluster(_Cluster):
    """ Uses Affinity Propagation to perform clustering """

    def cluster(self, x: List[T]) -> List[int]:
        # NB(nkansal96): The distance matrix is negated because smaller values means less similar
        #  but positive distance would indiate the opposite
        _, mapping = affinity_propagation(-self.get_distance_matrix(x))
        return mapping
