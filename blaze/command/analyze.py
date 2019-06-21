""" Implements the commands for analyzing training progress """
import json
import os
import sys
import tempfile

from blaze.action import Policy
from blaze.chrome.devtools import capture_har_in_mahimahi
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config, Config
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.record import record_webpage
from blaze.preprocess.resource import resource_list_to_push_groups

from . import command

EXECUTION_CAPTURE_RUNS = 5


@command.argument("url", nargs="?", help="The URL to analyze the page load time for")
@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator")
@command.argument(
    "--only_simulator",
    help="Only evaluate the page load time on the simulator (must be loaded from manifest to use this)",
)
@command.argument("--push_policy", help="The file path to a JSON-formatted push policy to simulate the PLT for")
@command.command
def page_load_time(args):
    """
    Captures a webpage and calculates the median page load time for a given website
    in a fast, no-latency Mahimahi shell. Then simulates the load based on profiling
    the page in the same Mahimahi shell.
    """
    # Validate the arguments
    if args.from_manifest and args.url:
        log.warn("ignoring url since manifest was specified")
    if not args.url and not args.from_manifest:
        log.critical("either --from_manifest or a URL must be specified")
        sys.exit(1)
    if args.only_simulator and not args.from_manifest:
        log.critical("--from_manifest must be specified to use with --only_simulator")
        sys.exit(1)

    log.info("calculating page load time", url=args.url)
    client_env = get_default_client_environment()

    def get_page_load_time_in_mahimahi(request_url: str, config: Config):
        log.debug("using client environment", **client_env._asdict())
        hars = []
        for i in range(EXECUTION_CAPTURE_RUNS):
            log.debug("recording page execution in Mahimahi", run=(i + 1), total_runs=EXECUTION_CAPTURE_RUNS)
            har = capture_har_in_mahimahi(request_url, config, client_env)
            hars.append(har)
            log.debug("captured page execution", page_load_time=har.page_load_time_ms)

        hars.sort(key=lambda h: h.page_load_time_ms)
        median_har = hars[len(hars) // 2]
        har_res_list = har_entries_to_resources(median_har)
        har_push_groups = resource_list_to_push_groups(har_res_list)
        return median_har.page_load_time_ms, har_res_list, har_push_groups

    if args.from_manifest:
        env_config = EnvironmentConfig.load_file(args.from_manifest)
        config = get_config(env_config)
        log.debug("using pre-recorded webpage", record_dir=config.env_config.replay_dir)
        plt, _, _ = get_page_load_time_in_mahimahi(config.env_config.request_url, config)

    else:
        with tempfile.TemporaryDirectory() as record_dir:
            # this is to work around the fact that mahimahi needs an empty directory
            # so we use TemporaryDirectory to get a unique name for a directory and
            # then delete it. After mahimahi runs and create the dir, then TemporaryDirectory
            # can delete it as normal
            os.rmdir(record_dir)
            config = get_config(EnvironmentConfig(replay_dir=record_dir, request_url=args.url))
            log.debug("recording webpage in Mahimahi", record_dir=record_dir)
            record_webpage(args.url, record_dir, config)

            plt, res_list, push_groups = get_page_load_time_in_mahimahi(config.env_config.request_url, config)
            env_config = EnvironmentConfig(
                replay_dir=record_dir, request_url=args.url, push_groups=push_groups, har_resources=res_list
            )

    policy = None
    if args.push_policy:
        log.debug("reading push policy", push_policy=args.push_policy)
        with open(args.push_policy, "r") as policy_file:
            policy_dict = json.load(policy_file)
        policy = Policy.from_dict(policy_dict)

    log.debug("running simulator...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env, policy)

    log.info("real page load time", page_load_time=plt)
    log.info("simulated page load time", page_load_time=sim_plt)
