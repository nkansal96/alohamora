from blaze.evaluator.cluster import Cluster
from blaze.evaluator.cluster.distance import linear_distance, euclidian_distance


class TestCluster:
    def test_1d_cluster(self):
        all_points = [1, 2, 3, 4, 10, 11, 13, 18, 19]

        c = Cluster(linear_distance)
        m = c.cluster(all_points)
        assert len(m) == len(all_points)
        assert len(set(m)) == 3
        assert m[0] == m[1] == m[2] == m[3]
        assert m[4] == m[5] == m[6]
        assert m[7] == m[8]
        assert m[0] != m[4] != m[7]

    def test_2d_cluster(self):
        all_points = [(1, 1), (1, 2), (2, 1), (3, 1), (6, 7), (6, 8), (6, 9), (1, 20), (2, 21)]

        c = Cluster(euclidian_distance)
        m = c.cluster(all_points)
        assert len(m) == len(all_points)
        assert len(set(m)) == 3
        assert m[0] == m[1] == m[2] == m[3]
        assert m[4] == m[5] == m[6]
        assert m[7] == m[8]
        assert m[0] != m[4] != m[7]
