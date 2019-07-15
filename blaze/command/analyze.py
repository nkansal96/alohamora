""" Implements the commands for analyzing training progress """
import json
import os
import sys
import tempfile

from blaze.action import Policy
from blaze.config.client import get_client_environment_from_parameters, get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import record_webpage, get_page_load_time_in_mahimahi

from . import command


@command.argument("url", nargs="?", help="The URL to analyze the page load time for")
@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator")
@command.argument(
    "--only_simulator",
    action="store_true",
    help="Only evaluate the page load time on the simulator (must be loaded from manifest to use this)",
)
@command.argument("--push_policy", help="The file path to a JSON-formatted push policy to simulate the PLT for")
@command.argument("--latency", help="The round trip latency to use (ms)", type=int, default=None)
@command.argument("--bandwidth", help="The link bandwidth to use (kbps)", type=int, default=None)
@command.argument("--cpu_slowdown", help="The CPU slowdown factor to use (1, 2, or 4)", type=int, default=None)
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
    if args.latency is not None and args.latency < 0:
        log.critical("provided latency must be greater or equal to 0")
        sys.exit(1)
    if args.bandwidth is not None and args.bandwidth <= 0:
        log.critical("provided bandwidth must be greater than 0")
        sys.exit(1)
    if args.cpu_slowdown is not None and args.cpu_slowdown not in {1, 2, 4}:
        log.critical("provided cpu slodown must be 1, 2, or 4")
        sys.exit(1)

    log.info("calculating page load time", url=args.url)
    default_client_env = get_default_client_environment()
    client_env = get_client_environment_from_parameters(
        args.bandwidth or default_client_env.bandwidth,
        args.latency or default_client_env.latency,
        args.cpu_slowdown or default_client_env.cpu_slowdown,
    )

    if args.from_manifest:
        env_config = EnvironmentConfig.load_file(args.from_manifest)
        config = get_config(env_config)
        if not args.only_simulator:
            log.debug("using pre-recorded webpage", record_dir=config.env_config.replay_dir)
            plt, _, _, _ = get_page_load_time_in_mahimahi(config.env_config.request_url, client_env, config)

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

            plt, res_list, push_groups, median_har = get_page_load_time_in_mahimahi(
                config.env_config.request_url, client_env, config
            )
            json.dump(
                {
                    "timings": {k: v._asdict() for (k, v) in median_har.timings.items()},
                    "page_load_time_ms": median_har.page_load_time_ms,
                },
                sys.stderr,
                indent=4,
            )
            sys.stderr.write("\n")
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

    if not args.only_simulator:
        log.info("real page load time", page_load_time=plt)
    log.info("simulated page load time", page_load_time=sim_plt)
