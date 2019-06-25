"""
This module implements functions to analyze data recorded in the train results
directory to provide some insight into speed index as it relates to the push
policy it was run with
"""

import collections
import glob
import json

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, NamedTuple

from blaze.config.client import ClientEnvironment
from blaze.logger import logger


class EvalResult(NamedTuple):
    raw: any
    url: str
    speed_index: float
    push_policy: Dict[str, List[str]]
    client_environment: ClientEnvironment

    @property
    def num_pushed(self):
        return sum(map(len, self.push_policy.values()))


def read_eval_result_files(results_dir: str) -> List[EvalResult]:
    results = []
    log = logger.with_namespace("analytics")
    json_files = glob.iglob("{}/*.json".format(results_dir))
    for i, file in enumerate(json_files):
        with open(file, "r") as f:
            json_data = json.load(f)
            eval_result = EvalResult(
                raw=json_data,
                url=json_data["url"],
                speed_index=float(json_data["speed_index"]),
                push_policy=json_data["policy"],
                client_environment=ClientEnvironment(**json_data["client_environment"]),
            )
            results.append(eval_result)
        if i % 1000 == 0 and i > 0:
            log.debug("loaded files", total=i)
            # break
    log.debug("Read eval result files", total=len(results), directory=results_dir)
    return results


def group_site_data(
    files: List[EvalResult], order=lambda r: r.num_pushed, pivot=lambda r: r.num_pushed, value=lambda r: r.speed_index
) -> Dict[str, Dict[int, List[float]]]:
    files = sorted(files, key=order)
    grouping = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in files:
        grouping[f.url][pivot(f)].append(value(f))
    return grouping


def best_eval_result(files: List[EvalResult], site: str) -> EvalResult:
    return min(filter(lambda r: r.url == site, files), key=lambda r: r.speed_index)


def analyze_train_results(results_dir: str):
    log = logger.with_namespace("analytics")
    log.info("reading files", eval_results_dir=results_dir)
    files = read_eval_result_files(results_dir)
    # fmt: off
    default_si = {
        'https://www.amazon.com': [8192, 8196, 8402, 9205, 8654],
        'https://www.apple.com': [7583, 7065, 6472, 4676, 6763, 7034, 6985, 6899, 6508, 6983, 6971, 6555, 6918, 4503, 6881],
        'https://www.bing.com': [1222, 1114, 1113, 1168, 1124, 1213, 1269, 1132, 1188, 1128, 1132, 1114, 1161, 1099, 1171, 1084, 1240, 1100, 1143, 1161, 1153, 1181, 1128, 1151, 1212, 1192, 1206, 1136, 1173, 1159, 1108, 1145, 1089, 1134, 1090],
        # 'https://www.buzzfeed.com': [4908, 4830, 4524, 5073, 5875, 4786, 6118, 5325, 5254, 4820, 5487, 5821, 4750, 8020, 5195],
        'https://www.buzzfeed.com': [
            3390,
            3415,
            3457,
            3480,
            3518,
            3547,
            3586,
            3593,
            3604,
            3608,
            3626,
            3651,
            3726,
            3728,
            3733,
            3749,
            3773,
            3823,
            3830,
            3845,
            3853,
            3857,
            3861,
            3862,
            3876,
            3888,
            3894,
            3920,
            3942,
            3947,
            3970,
            3975,
            3987,
            4000,
            4003,
            4035,
            4079,
            4135,
            4145,
            4195,
            4198,
            4201,
            4210,
            4231,
            4269,
            4270,
            4322,
            4339,
            4371,
            4442,
            4459
        ],
        'https://www.cnn.com': [13765, 15719, 15046, 14101, 15214, 13978, 14179, 14154, 13986, 15181, 13864, 13134, 15933, 15235, 15652,],
        'https://www.pinterest.com': [12739, 10061, 9736, 10021, 10418, 9616, 10025, 10523, 10540, 10817, 10323, 9697, 10005, 10060, 10535],
        'https://www.reddit.com': [11045, 11795, 10053, 12826, 10849, 11045, 10291, 8393, 10442, 10079, 10527, 12168, 9890, 10038],
        'https://www.yelp.com': [5953, 4188, 4979, 4783, 3630, 4192, 5458, 4615, 4394, 4889, 4525, 5090, 4961, 4971, 6049, 3878, 4652, 5301, 4887, 3968, 5597, 4842, 5093, 4008, 4961],
        'https://www.wikipedia.org': [1552, 1698, 1609, 1559, 1398, 1611, 1679, 1577, 1687, 1610, 1621, 1651, 1712, 1539, 1773, 1804, 1629, 1674, 1709, 1902, 1810, 1673, 1633, 1653, 1904],
    }
    # fmt: on

    log.info("creating histograms")
    histograms = group_site_data(
        files, pivot=lambda r: (r.client_environment.latency // 10, r.client_environment.bandwidth // 1000)
    )
    for (site, latency_bandwidth_hist) in histograms.items():
        site_log = log.with_context(site=site)
        site_log.info("analyzing site")
        site_clean = site.replace(".", "_").replace("https://", "")

        for (lb, si_hist) in latency_bandwidth_hist.items():
            plt.figure(figsize=(18, 10), dpi=120)
            plt.hist(si_hist)
            plt.axvline(x=np.percentile(default_si[site], 25), color="#00ff00")  # green
            plt.axvline(x=np.percentile(default_si[site], 50), color="#ff7f50")  # orange
            plt.axvline(x=np.percentile(default_si[site], 75), color="#ff4500")  # red
            plt.title(f"{site} ({lb[0]}0 ms, {lb[1]} mbps)")
            plt.ylabel("Number of Policies")
            plt.xlabel("Speed Index")
            plt.savefig("/Users/nkansal/Desktop/out5/lb_hists/{}_{}0ms_{}mbps.jpg".format(site_clean, lb[0], lb[1]))
            plt.close()
            # site_log.debug("created boxplot")

    histograms = group_site_data(files)
    for (site, si_hist) in histograms.items():
        site_log = log.with_context(site=site)
        site_log.info("analyzing site")
        site_clean = site.replace(".", "_").replace("https://", "")

        data = [y for x in si_hist.values() for y in x]
        plt.figure(figsize=(18, 10), dpi=120)
        plt.title(site)
        _, bins, _ = plt.hist(x=data, bins="auto", orientation="vertical")

        num_pushed_dists = []
        for bin_left, bin_right in zip(bins[:-1], bins[1:]):
            num_pushed_dists.append(
                ((bin_right + bin_left) / 2, [r.num_pushed for r in files if bin_left <= r.speed_index <= bin_right])
            )

        plt.ylabel("Number of Policies")
        plt.xlabel("Speed Index")
        plt.axvline(x=np.percentile(default_si[site], 25), color="#00ff00")  # green
        plt.axvline(x=np.percentile(default_si[site], 50), color="#ff7f50")  # orange
        plt.axvline(x=np.percentile(default_si[site], 75), color="#ff4500")  # red
        plt.savefig("/Users/nkansal/Desktop/out5/hist_{}.jpg".format(site_clean))
        plt.close()

        plt.figure(figsize=(18, 10), dpi=120)
        plt.boxplot([x[1] for x in num_pushed_dists])
        plt.title(site)
        plt.xlabel("Speed Index")
        plt.ylabel("Number of Resources Pushed")
        plt.savefig("/Users/nkansal/Desktop/out2/hist_boxplot_{}.jpg".format(site_clean))
        plt.close()
        site_log.debug("created histogram")

        best = best_eval_result(files, site)
        with open("/Users/nkansal/Desktop/out5/best_{}.json".format(site_clean), "w") as best_out_file:
            json.dump(best.raw, best_out_file, indent=2)
        site_log.debug("wrote best eval result")
