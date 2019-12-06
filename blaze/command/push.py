""" Implements the commands for analyzing training progress """
import collections
import json
import random
import urllib
import subprocess
import traceback
from typing import Callable, List, Optional, Tuple

from blaze.action import Policy
from blaze.config.client import (
    get_client_environment_from_parameters,
    get_default_client_environment,
    ClientEnvironment,
)
from blaze.config.config import get_config, Config
from blaze.config.environment import EnvironmentConfig, ResourceType
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import get_page_load_time_in_replay_server, get_speed_index_in_replay_server

from . import command


@command.argument(
    "--policy_type", help="The test type to run", choices=["push", "push_preload", "preload", "all"], required=True
)
@command.argument("--from_manifest", required=True, help="The training manifest file to use as input to the simulator")
@command.command
def random_push_policy(args):
    """
    Outputs a random push policy for the given recorded website
    """
    log.info("generating a random policy", policy_type=args.policy_type)
    env_config = EnvironmentConfig.load_file(args.from_manifest)

    weight = 0 if args.policy_type == "preload" else 1 if args.policy_type == "push" else None
    policy = _random_push_preload_policy_generator(weight)(env_config)

    print(json.dumps(policy.as_dict, indent=4))


@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator", required=True)
@command.argument("--only_simulator", action="store_true", help="Only evaluate the page load time on the simulator")
@command.argument(
    "--policy_type", help="The test type to run", choices=["push", "push_preload", "preload"], required=True
)
@command.argument("--iterations", help="Number of trials", type=int, default=1)
@command.argument("--max_retries", help="Maximum number of times to retry failed runs", type=int, default=0)
@command.argument("--bandwidth", help="Link bandwidth to simulate (kbps)", type=int, default=None)
@command.argument("--latency", help="Link RTT to simulate (ms)", type=int, default=None)
@command.argument(
    "--cpu_slowdown", help="CPU Slowdown factor (1 means no slowdown)", choices=[1, 2, 4], type=int, default=1
)
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
@command.command
def test_push(args):
    """
    Runs a pre-defined test on the given webpage
    """
    if args.policy_type == "all":
        policy_generator = push_preload_all_policy_generator()
    else:
        weight = 0 if args.policy_type == "preload" else 1 if args.policy_type == "push" else None
        policy_generator = _random_push_preload_policy_generator(weight)

    _test_push(
        manifest=args.from_manifest,
        iterations=args.iterations,
        max_retries=args.max_retries,
        policy_generator=policy_generator,
        bandwidth=args.bandwidth,
        latency=args.latency,
        cpu_slowdown=args.cpu_slowdown,
        only_simulator=args.only_simulator,
        speed_index=args.speed_index,
        user_data_dir=args.user_data_dir,
    )
    return 0


def push_preload_all_policy_generator() -> Callable[[EnvironmentConfig], Policy]:
    """
    Returns a generator than always choose to push/preload all assets
    Push all in same domain. Preload all in other domains.
    """

    def _generator(env_config: EnvironmentConfig) -> Policy:
        push_groups = env_config.push_groups
        # Collect all resources and group them by type
        all_resources = sorted([res for group in push_groups for res in group.resources], key=lambda res: res.order)
        # choose the weight factor between push and preload
        main_domain = urllib.parse.urlparse(env_config.request_url)
        policy = Policy()
        for r in all_resources:
            if r.source_id == 0 or r.order == 0:
                continue
            request_domain = urllib.parse.urlparse(r.url)
            push = request_domain.netloc == main_domain.netloc
            policy.steps_taken += 1
            if push:
                source = random.randint(0, r.source_id - 1)
                policy.add_default_push_action(push_groups[r.group_id].resources[source], r)
            else:
                source = random.randint(0, r.order - 1)
                policy.add_default_preload_action(all_resources[source], r)
        return policy

    return _generator


def _random_push_preload_policy_generator(push_weight: Optional[float] = None) -> Callable[[EnvironmentConfig], Policy]:
    dist = {ResourceType.SCRIPT: 32, ResourceType.CSS: 32, ResourceType.IMAGE: 24, ResourceType.FONT: 12}

    def _choose_with_dist(groups, distribution):
        subdist = sorted([(k, distribution[k]) for k in groups if groups[k]])
        sorted_groups = sorted([(k, v) for (k, v) in groups.items() if v])
        g, random_group = random.choices(sorted_groups, weights=[s[1] for s in subdist])[0]
        r = random.randrange(0, len(random_group))
        return g, r, random_group[r]

    def _generator(env_config: EnvironmentConfig) -> Policy:
        push_groups = env_config.push_groups
        # Collect all resources and group them by type
        all_resources = sorted([res for group in push_groups for res in group.resources], key=lambda res: res.order)
        res_by_type = collections.defaultdict(list)
        for res in all_resources:
            # Only consider objects in the push resource type distribution
            if res.type in dist:
                res_by_type[res.type].append(res)

        # choose the number of resources to push/preload
        total = sum(map(len, res_by_type.values()))
        n = random.randint(1, total)
        # choose the weight factor between push and preload
        weight = push_weight if push_weight is not None else random.random()

        # Choose n resources based on the resource type distribution without replacement
        log.debug("generating push-preload policy", num_resources=len(all_resources), total_size=n, push_weight=weight)
        res = []
        for _ in range(n):
            g, r, s = _choose_with_dist(res_by_type, dist)
            res_by_type[g].pop(r)
            res.append(s)

        policy = Policy()

        for r in res:
            if r.source_id == 0 or r.order == 0:
                continue
            push = random.random() < weight
            policy.steps_taken += 1
            if push:
                source = random.randint(0, r.source_id - 1)
                policy.add_default_push_action(push_groups[r.group_id].resources[source], r)
            else:
                source = random.randint(0, r.order - 1)
                policy.add_default_preload_action(all_resources[source], r)

        return policy

    return _generator


def _test_push(
    *,
    manifest: str,
    iterations: Optional[int] = 1,
    max_retries: Optional[int] = 0,
    policy_generator: Callable[[EnvironmentConfig], Policy],
    bandwidth: Optional[int],
    latency: Optional[int],
    cpu_slowdown: Optional[int],
    only_simulator: Optional[bool],
    speed_index: Optional[bool],
    user_data_dir: Optional[str],
):
    env_config = EnvironmentConfig.load_file(manifest)
    default_client_env = get_default_client_environment()
    client_env = get_client_environment_from_parameters(
        bandwidth or default_client_env.bandwidth,
        latency or default_client_env.latency,
        cpu_slowdown or default_client_env.cpu_slowdown,
    )

    data = {
        "client_env": client_env._asdict(),
        "url": env_config.request_url,
        "cache": "warm" if user_data_dir else "cold",
        "metric": "speed_index" if speed_index else "plt",
    }

    if not only_simulator:
        config = get_config(env_config)
        plt, push_plts, policies = _get_results_in_replay_server(
            config, client_env, iterations, max_retries, policy_generator, user_data_dir, speed_index
        )
        data["replay_server"] = {
            "without_policy": plt,
            "with_policy": [{"plt": plt, "policy": policy.as_dict} for (plt, policy) in zip(push_plts, policies)],
        }

    else:
        policies = [policy_generator(env_config) for _ in range(iterations)]

    sim = Simulator(env_config)
    data["simulator"] = {
        "without_policy": sim.simulate_load_time(client_env),
        "with_policy": [
            {"plt": sim.simulate_load_time(client_env, policy), "policy": policy.as_dict} for policy in policies
        ],
    }

    print(json.dumps(data, indent=4))


def _get_results_in_replay_server(
    config: Config,
    client_env: ClientEnvironment,
    iterations: int,
    max_retries: int,
    policy_generator: Callable[[EnvironmentConfig], Policy],
    user_data_dir: Optional[str] = None,
    speed_index: Optional[bool] = False,
) -> Tuple[float, List[float], List[Policy]]:
    log.debug("capturing median PLT in mahimahi with given environment")
    if not speed_index:
        orig_plt, *_ = get_page_load_time_in_replay_server(
            config.env_config.request_url, client_env, config, user_data_dir
        )
    else:
        orig_plt = get_speed_index_in_replay_server(config.env_config.request_url, client_env, config, user_data_dir)

    plts = []
    policies = []
    retries = 0

    while retries <= max_retries and len(plts) < iterations:
        policy = policy_generator(config.env_config)

        log.debug("getting HAR in mahimahi with policy:")
        log.debug(json.dumps(policy.as_dict, indent=4))

        try:
            if not speed_index:
                plt, *_ = get_page_load_time_in_replay_server(
                    config.env_config.request_url, client_env, config, user_data_dir, policy
                )
            else:
                plt = get_speed_index_in_replay_server(
                    config.env_config.request_url, client_env, config, user_data_dir, policy
                )
            plts.append(plt)
            policies.append(policy)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
            log.warn("replay_server failed:", i=len(plts), retries=retries, error=repr(e))
            traceback.print_exc()
            retries += 1

    return orig_plt, plts, policies
