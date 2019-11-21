""" Implements distance functions for the """
import json
import math
from typing import Dict, List

import requests

from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator

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
        a_tree = json.dumps(get_apted_tree(a))
        b_tree = json.dumps(get_apted_tree(b))
        r = requests.get(f"http://localhost:{port}/getTreeDiff", params={"tree1": a_tree, "tree2": b_tree}).json()
        return r["editDistance"]

    return apted_distance
