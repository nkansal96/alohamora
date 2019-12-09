""" Implements the commands for analyzing training progress """
import json
import sys

from blaze.action import Policy
from blaze.config.client import get_client_environment_from_parameters, get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import get_page_load_time_in_replay_server, get_speed_index_in_replay_server

from . import command


@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator", required=True)
@command.argument(
    "--only_simulator",
    action="store_true",
    help="Only evaluate the page load time on the simulator (must be loaded from manifest to use this)",
)
@command.argument("--policy", help="The file path to a JSON-formatted push/preload policy to simulate the PLT for")
@command.argument("--latency", help="The round trip latency to use (ms)", type=int, default=None)
@command.argument("--bandwidth", help="The link bandwidth to use (kbps)", type=int, default=None)
@command.argument("--cpu_slowdown", help="The CPU slowdown factor to use (1, 2, or 4)", type=int, default=None)
@command.argument(
    "--user_data_dir",
    help="The Chrome user data directory contains cached files (in case of using warm cache)",
    type=str,
    default=None,
)
@command.argument(
    "--speed_index",
    help="Returns the speed index of the page calculated using pwmetrics. As a float.",
    action="store_true",
)
@command.argument(
    "--cache_time", help="Simulate cached object expired after this time (in seconds)", type=int, default=None
)
@command.command
def page_load_time(args):
    """
    Captures a webpage and calculates the median page load time for a given website
    in a fast, no-latency Mahimahi shell. Then simulates the load based on profiling
    the page in the same Mahimahi shell.
    """
    # Validate the arguments
    if args.latency is not None and args.latency < 0:
        log.critical("provided latency must be greater or equal to 0")
        sys.exit(1)
    if args.bandwidth is not None and args.bandwidth <= 0:
        log.critical("provided bandwidth must be greater than 0")
        sys.exit(1)
    if args.cpu_slowdown is not None and args.cpu_slowdown not in {1, 2, 4}:
        log.critical("provided cpu slodown must be 1, 2, or 4")
        sys.exit(1)

    # Setup the client environment
    default_client_env = get_default_client_environment()
    client_env = get_client_environment_from_parameters(
        args.bandwidth or default_client_env.bandwidth,
        args.latency or default_client_env.latency,
        args.cpu_slowdown or default_client_env.cpu_slowdown,
    )

    # If a push/preload policy was specified, read it
    policy = None
    if args.policy:
        log.debug("reading policy", push_policy=args.policy)
        with open(args.policy, "r") as policy_file:
            policy_dict = json.load(policy_file)
        policy = Policy.from_dict(policy_dict)

    env_config = EnvironmentConfig.load_file(args.from_manifest)
    config = get_config(env_config)

    log.info("calculating page load time", manifest=args.from_manifest, url=env_config.request_url)
    plt, orig_plt = 0, 0
    if not args.only_simulator:
        if not args.speed_index:
            orig_plt, *_ = get_page_load_time_in_replay_server(
                request_url=config.env_config.request_url,
                client_env=client_env,
                config=config,
                cache_time=args.cache_time,
                user_data_dir=args.user_data_dir,
            )
            if policy:
                plt, *_ = get_page_load_time_in_replay_server(
                    request_url=config.env_config.request_url,
                    client_env=client_env,
                    config=config,
                    policy=policy,
                    cache_time=args.cache_time,
                    user_data_dir=args.user_data_dir,
                )
        else:
            orig_plt = get_speed_index_in_replay_server(
                request_url=config.env_config.request_url,
                client_env=client_env,
                config=config,
                cache_time=args.cache_time,
                user_data_dir=args.user_data_dir,
            )
            if policy:
                plt = get_speed_index_in_replay_server(
                    request_url=config.env_config.request_url,
                    client_env=client_env,
                    config=config,
                    policy=policy,
                    cache_time=args.cache_time,
                    user_data_dir=args.user_data_dir,
                )

    log.debug("running simulator...")
    sim = Simulator(env_config)
    orig_sim_plt = sim.simulate_load_time(client_env)
    sim_plt = sim.simulate_load_time(client_env, policy)

    print(
        json.dumps(
            {
                "client_env": client_env._asdict(),
                "metric": "speed_index" if args.speed_index else "plt",
                "cache": "warm" if args.user_data_dir else "cold",
                "cache_time": args.cache_time,
                "replay_server": {"with_policy": plt, "without_policy": orig_plt},
                "simulator": {"with_policy": sim_plt, "without_policy": orig_sim_plt},
            },
            indent=4,
        )
    )
