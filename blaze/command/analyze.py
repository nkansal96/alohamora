""" Implements the commands for analyzing training progress """
import os
import tempfile

from blaze.chrome.devtools import capture_har_in_mahimahi
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.record import record_webpage
from blaze.preprocess.resource import resource_list_to_push_groups

from . import command

EXECUTION_CAPTURE_RUNS = 5


@command.argument("url", help="The URL to analyze the page load time for")
@command.argument("--from_record_dir", help="The recorded webpage to use as the baseline PLT")
@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator")
@command.command
def page_load_time(args):
    """
    Captures a webpage and calculates the median page load time for a given website
    in a fast, no-latency Mahimahi shell. Then simulates the load based on profiling
    the page in the same Mahimahi shell.
    """
    log.info("calculating page load time", url=args.url)
    client_env = get_default_client_environment()

    with tempfile.TemporaryDirectory() as tmp_record_dir:
        # this is to work around the fact that mahimahi needs an empty directory
        # so we use TemporaryDirectory to get a unique name for a directory and
        # then delete it. After mahimahi runs and create the dir, then TemporaryDirectory
        # can delete it as normal
        record_dir = args.from_record_dir or tmp_record_dir
        config = get_config(EnvironmentConfig(replay_dir=record_dir, request_url=args.url))
        if not args.from_record_dir:
            log.info("recording webpage in Mahimahi")
            os.rmdir(record_dir)
            record_webpage(args.url, record_dir, config)

        else:
            log.info("using pre-recorded webpage", record_dir=record_dir)

        log.debug("using client environment", **client_env._asdict())
        hars = []
        for i in range(EXECUTION_CAPTURE_RUNS):
            log.info("recording page execution in Mahimahi", run=(i + 1), total_runs=EXECUTION_CAPTURE_RUNS)
            har = capture_har_in_mahimahi(args.url, config, client_env)
            hars.append(har)
            log.debug("captured page execution", page_load_time=har.page_load_time_ms)

        hars.sort(key=lambda h: h.page_load_time_ms)
        median_har = hars[len(hars) // 2]
        res_list = har_entries_to_resources(median_har)
        push_groups = resource_list_to_push_groups(res_list)
        log.debug("chose har", num_resources=len(res_list), page_load_time_ms=har.page_load_time_ms)

    if not args.from_manifest:
        env_config = EnvironmentConfig(
            replay_dir="", request_url=args.url, push_groups=push_groups, har_resources=res_list
        )
    else:
        env_config = EnvironmentConfig.load_file(args.from_manifest)

    log.info("simulating page load time...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env)

    log.info("real page load time", page_load_time=har.page_load_time_ms)
    log.info("simulated page load time", page_load_time=sim_plt)
