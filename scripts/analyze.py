#! /usr/bin/env python3

import collections
import json
import os
import pprint
import sys


def get_best_pct_diff(a, b):
    return round(100 * min(filter(lambda d: d > -0.7, ((bi - ai) / ai for (ai, bi) in zip(a, b)))), 3)


def get_best_val_pair(a, b):
    m, n = 0, 100
    for (ai, bi) in zip(a, b):
        new_n = (bi - ai) / ai
        if new_n < n and new_n > -0.7:
            m = (ai, bi)
            n = new_n
    return m


folder = sys.argv[1]
file_paths = [os.path.join(folder, f) for f in os.listdir(folder)]
result_files = list(map(json.load, (open(f, "rb") for f in file_paths)))

results_by_env = collections.defaultdict(list)
for result, path in zip(result_files, file_paths):
    results_by_env[path[-17:]].append(result)

results_map = {}
for env, results in results_by_env.items():
    pct_diff = sorted(
        [get_best_pct_diff(a["replay_server"]["without_policy"], a["replay_server"]["with_policy"]) for a in results]
    )
    replay_without_policy, replay_with_policy = list(
        map(
            sorted,
            zip(
                *[
                    get_best_val_pair(a["replay_server"]["without_policy"], a["replay_server"]["with_policy"])
                    for a in results
                ]
            ),
        )
    )
    simulator_without_policy = sorted([a["simulator"]["without_policy"] for a in results])
    simulator_with_policy = sorted([a["simulator"]["with_policy"] for a in results])
    results_map[env] = {
        "pct_diff": pct_diff,
        "replay_server": {"without_policy": replay_without_policy, "with_policy": replay_with_policy},
        "simulator": {"without_policy": simulator_without_policy, "with_policy": simulator_with_policy},
    }

print(json.dumps(results_map, indent=4))
