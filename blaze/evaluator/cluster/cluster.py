""" Main clustering logic """
import abc
import collections
from typing import Generic, List

import numpy as np
from sklearn.cluster import AgglomerativeClustering, dbscan

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


class AgglomerativeCluster(_Cluster):
    """ Uses Agglomerative Clustering to perform clustering """

    def cluster(self, x: List[T]) -> List[int]:
        distance_matrix = self.get_distance_matrix(x)

        def pairwise_distances(p):
            return [distance_matrix[p[k]][p[y]] for k in range(len(p)) for y in range(k + 1, len(p))]

        max_num_clusters = len(x) - 1
        best_labels = [0]
        best_score = 1000000000

        for c in range(2, max_num_clusters):
            a = AgglomerativeClustering(n_clusters=c, affinity="precomputed", linkage="average").fit(distance_matrix)
            labels = a.labels_

            cluster_points = collections.defaultdict(list)
            for i, label in enumerate(labels.tolist()):
                cluster_points[label].append(i)

            variances = [np.var(pairwise_distances(points)) for points in cluster_points.items()]
            score = 0.5 * c + np.var(variances)

            if score < best_score:
                best_score = score
                best_labels = labels

        return best_labels
