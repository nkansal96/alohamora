""" Implements distance functions for clustering """
import math
from typing import Dict, List

import requests

from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log

from .types import DistanceFunc


def linear_distance(a: float, b: float) -> float:
    """ Returns the absolute difference between a and b """
    return abs(a - b)


def euclidian_distance(a: List[float], b: List[float]) -> float:
    """ Returns the euclidian distance between two N-dimensional points """
    return math.sqrt(sum((x - y) ** 2 for (x, y) in zip(a, b)))


def create_apted_distance_function(port: int) -> DistanceFunc:
    """ Creates a distance function with a connection to the tree_diff server """

    def get_apted_tree(env_config: EnvironmentConfig) -> Dict:
        sim = Simulator(env_config)
        tree = {}
        s = [sim.root]
        while s:
            curr = s.pop()
            tree[curr.priority] = {
                "size": curr.resource.size,
                "type": str(curr.resource.type),
                "children": [c.priority for c in curr.children],
            }
            s.extend(curr.children)
        tree["length"] = len(tree)
        return tree

    def apted_distance(a: EnvironmentConfig, b: EnvironmentConfig) -> float:
        a_tree = get_apted_tree(a)
        b_tree = get_apted_tree(b)
        r = requests.post(f"http://localhost:{port}/getTreeDiff", json={"tree1": a_tree, "tree2": b_tree}, timeout=5)
        r = r.json()
        distance = r["editDistance"]
        log.with_namespace("apted_distance").debug("got distance", distance=distance, a=a.request_url, b=b.request_url)
        return distance

    return apted_distance
