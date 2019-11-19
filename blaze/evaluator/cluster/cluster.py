""" Main clustering logic """
from typing import Generic, List

import numpy as np
from sklearn.cluster import dbscan

from .types import T, DistanceFunc


class Cluster(Generic[T]):
    """
    Implements a clustering algorithm that takes a list of elements and a distance function that returns the
    distance between any two objects in the list.
    """

    def __init__(self, distance_func: DistanceFunc):
        """ Initialize the Cluster object with a distance function """
        self.distance_func = distance_func

    def get_distance_matrix(self, x: List[T]) -> np.array:
        """ Returns an NxN matrix precomputed with the pairwise distances between all objects in the list """
        # TODO: this can be optimized to remove repeated calls ((i, j) and (j, i), and unnecessary calls (i, i)
        return np.array([[self.distance_func(x[i], x[j]) for j in range(len(x))] for i in range(len(x))])

    def cluster(self, x: List[T]) -> List[int]:
        """ Returns a list the same as as the input list with cluster labels corresponding to each element """
        # TODO: figure out how to set `eps` optimally
        _, mapping = dbscan(self.get_distance_matrix(x), eps=2, min_samples=0, metric="precomputed")
        return mapping
