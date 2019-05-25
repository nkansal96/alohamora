"""
This module implements functions to analyze data recorded in the train results
directory to provide some insight into speed index as it relates to the push
policy it was run with
"""

import collections
import glob
import json
import pprint

import matplotlib.pyplot as plt
import numpy as np

from blaze.logger import logger

def read_train_result_files(results_dir: str):
    files = []
    for fname in glob.glob("{}/*.json".format(results_dir)):
        with open(fname, 'r') as f:
            files.append(json.load(f))
    logger.with_namespace("analytics").debug("Read file", total=len(files), directory=results_dir)
    return files

def build_domain_histograms(files):
    data = {}
    for f in files:
        if f['url'] not in data:
            data[f['url']] = collections.defaultdict(list)
        r_len = len(set(u for v in f['policy'].values() for u in v))
        data[f['url']][r_len].append(f['speedIndex'])
    # for url, r_map in data.items():

    return data

def analyze_train_results(results_dir: str, site: str):
    files = read_train_result_files(results_dir)
    histograms = build_domain_histograms(files)
    base = {
        'https://www.apple.com': [
            7583, 7065, 6472, 4676, 6763, 7034, 6985, 6899, 6508, 6983, 6971, 6555, 6918, 4503, 6881,
        ],
        'https://www.pinterest.com': [
            12739, 10061, 9736, 10021, 10418, 9616, 10025, 10523, 10540, 10817, 10323, 9697, 10005, 10060, 10535,
        ],
        'https://www.cnn.com': [
            13765, 15719, 15046, 14101, 15214, 13978, 14179, 14154, 13986, 15181, 13864, 13134, 15933, 15235, 15652,
        ],
        'https://www.reddit.com': [
            11045, 11795, 10053, 12826, 10849, 11045, 10291, 8393, 10442, 10079, 10527, 12168, 9890, 10038,
        ],
        'https://www.buzzfeed.com': [
            4908, 4830, 4524, 5073, 5875, 4786, 6118, 5325, 5254, 4820, 5487, 5821, 4750, 8020, 5195,
        ],
    }

    for s in base:
        hist = [x[1] for x in sorted([(0, base[s]), *list(histograms[s].items())])]
        # print(list(map(len, hist)))
        # print(list(map(np.median, hist)))
        # print(list(map(np.min, hist)))
        plt.figure(figsize=(18, 10), dpi=120)
        plt.boxplot(hist)
        plt.title(s)
        plt.ylabel("Speed Index")
        plt.xlabel("Number of Resources Pushed")
        plt.xticks(list(range(1, len(hist) + 1)), list(range(len(hist))))
        plt.savefig("/Users/nkansal/Desktop/boxplot_{}.jpg".format(s.replace(".", "_").replace("https://", "")))
        # plt.show()
