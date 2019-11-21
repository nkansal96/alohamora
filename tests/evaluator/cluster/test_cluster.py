from blaze.evaluator.cluster import AgglomerativeCluster, DBSSCANCluster
from blaze.evaluator.cluster.distance import linear_distance, euclidian_distance

TEST_CASES = [
    ("1d_cluster", linear_distance, [1, 2, 3, 4, 10, 11, 13, 18, 19], [0, 0, 0, 0, 1, 1, 1, 2, 2]),
    (
        "2d_cluster",
        euclidian_distance,
        [(1, 1), (1, 2), (2, 1), (3, 1), (6, 7), (6, 8), (6, 9), (1, 20), (2, 21)],
        [0, 0, 0, 0, 1, 1, 1, 2, 2],
    ),
    ("close_cluster", linear_distance, [1, 1, 5, 5, 6], [0, 0, 1, 1, 1]),
]


def is_one_to_one(a, b) -> bool:
    if len(a) != len(b):
        return False

    mapping = {}
    for (x, y) in zip(a, b):
        if x in mapping and mapping[x] != y:
            return False
        if x not in mapping:
            mapping[x] = y

    return True


class TestAgglomerativeCluster:
    def test(self):
        for (name, distance_func, points, labels) in TEST_CASES:
            c = AgglomerativeCluster(distance_func)
            m = c.cluster(points)
            assert len(m) == len(points), f"{name}: len(m) != len(points)"
            assert len(set(m)) == len(set(labels)), f"{name}: len(set(m)) != len(set(labels))"
            assert is_one_to_one(labels, m), f"{name}: labels do not match"
