#! /usr/bin/env python3

import collections
import json
import os
import pprint
import sys


def pct_diff(a, b):
    return (a - b) / b


def get_best_pct_diff(a, b):
    return round(100 * min(filter(lambda d: d > -0.8, (pct_diff(bi, ai) for (ai, bi) in zip(a, b)))), 3)


def get_best_val_pair(a, b):
    m, n = 0, 100
    for (ai, bi) in zip(a, b):
        new_n = pct_diff(bi, ai)
        if -0.8 < new_n < n:
            m = (ai, bi)
            n = new_n
    return m


folders = sys.argv[1:]
file_paths = [os.path.join(folder, f) for folder in folders for f in os.listdir(folder) if f.endswith(".json")]
result_files = []

for f in file_paths:
    try:
        result_files.append(json.load(open(f, "rb")))
    except json.JSONDecodeError as e:
        print("failed to decode json for " + f + ", err: " + str(e), file=sys.stderr)

results_by_env = collections.defaultdict(list)
for result, path in zip(result_files, file_paths):
    env = (result["client_env"]["bandwidth"], result["client_env"]["latency"], result["client_env"]["cpu_slowdown"])
    env_str = f"{env[0]//1000}mbps_{env[1]}ms_{env[2]}x"
    results_by_env[env_str].append(result)

results_map = {}
for env, results in results_by_env.items():
    replay_pct_diff = sorted(
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
    simulator_pct_diff = sorted(
        [100 * pct_diff(a["simulator"]["with_policy"], a["simulator"]["without_policy"]) for a in results]
    )
    simulator_without_policy = sorted([a["simulator"]["without_policy"] for a in results])
    simulator_with_policy = sorted([a["simulator"]["with_policy"] for a in results])
    results_map[env] = {
        "replay_server": {
            "pct_diff": replay_pct_diff,
            "without_policy": replay_without_policy,
            "with_policy": replay_with_policy,
        },
        "simulator": {
            "pct_diff": simulator_pct_diff,
            "without_policy": simulator_without_policy,
            "with_policy": simulator_with_policy,
        },
    }

print(json.dumps(results_map, indent=4))
