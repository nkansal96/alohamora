""" Implements the commands for analyzing training progress """
import collections
import json
import os
import random
import tempfile
from typing import Callable, List, Optional

from blaze.action import Policy
from blaze.config.client import (
    get_client_environment_from_parameters,
    get_default_client_environment,
    ClientEnvironment,
)
from blaze.config.config import get_config, Config
from blaze.config.environment import EnvironmentConfig, PushGroup, ResourceType
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import capture_har_in_replay_server, record_webpage, get_page_load_time_in_replay_server
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups
from . import command


@command.argument(
    "--policy_type", help="The test type to run", choices=["simple", "push", "push_preload", "preload"], required=True
)
@command.argument("--from_manifest", required=True, help="The training manifest file to use as input to the simulator")
@command.command
def random_push_policy(args):
    """
    Outputs a random push policy for the given recorded website
    """
    log.info("generating a random policy", policy_type=args.policy_type)
    env_config = EnvironmentConfig.load_file(args.from_manifest)

    if args.policy_type == "simple":
        policy = _simple_push_policy_generator()(env_config.push_groups)
    else:
        weight = 0 if args.policy_type == "preload" else 1 if args.policy_type == "push" else None
        policy = _random_push_preload_policy_generator(weight)(env_config.push_groups)

    print(json.dumps(policy.as_dict, indent=4))


@command.argument("url", nargs="?", help="The URL to analyze the page load time for")
@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator")
@command.argument(
    "--only_simulator",
    action="store_true",
    help="Only evaluate the page load time on the simulator (must be loaded from manifest to use this)",
)
@command.argument(
    "--policy_type", help="The test type to run", choices=["simple", "push", "push_preload"], default="random"
)
@command.argument(
    "--random_chance",
    help="Probability of pushing a particular resource (only used for --policy_type=push). If not specified, the "
    "chance is generated randomly each time a random policy is generated.",
    type=float,
    default=None,
)
@command.argument("--iterations", help="Number of trials", type=int, default=1)
@command.argument("--bandwidth", help="Link bandwidth to simulate (kbps)", type=int, default=None)
@command.argument("--latency", help="Link RTT to simulate (ms)", type=int, default=None)
@command.argument(
    "--cpu_slowdown", help="CPU Slowdown factor (1 means no slowdown)", choices=[1, 2, 4], type=int, default=1
)
@command.command
def test_push(args):
    """
    Runs a pre-defined test on the given webpage
    """
    if not args.url and not args.from_manifest:
        log.error("must provide either a URL or a manifest")
        return 1
    if args.random_chance and (args.random_chance <= 0 or args.random_chance > 1):
        log.error("chance must be a float in the interval (0, 1]")
        return 1
    if args.only_simulator and not args.from_manifest:
        log.error("must specify a manifest if loading only simulator")
        return 1

    if args.policy_type == "simple":
        policy_generator = _simple_push_policy_generator()
    else:
        weight = 0 if args.policy_type == "preload" else 1 if args.policy_type == "push" else None
        policy_generator = _random_push_preload_policy_generator(weight)

    _test_push(
        **{
            "url": args.url,
            "manifest": args.from_manifest,
            "iterations": 1 if args.policy_type == "simple" else args.iterations,
            "policy_generator": policy_generator,
            "bandwidth": args.bandwidth,
            "latency": args.latency,
            "cpu_slowdown": args.cpu_slowdown,
            "only_simulator": args.only_simulator,
        }
    )
    return 0


def _simple_push_policy_generator() -> Callable[[List[PushGroup]], Policy]:
    def _generator(push_groups: List[PushGroup]) -> Policy:
        group = max(push_groups, key=lambda g: len(g.resources))
        source_res = min(group.resources, key=lambda r: r.order)
        push_res = min(
            (
                r
                for r in group.resources
                if r != source_res
                and r.type in {ResourceType.SCRIPT, ResourceType.CSS, ResourceType.IMAGE, ResourceType.FONT}
            ),
            key=lambda r: r.size,
        )
        policy = Policy()
        policy.add_default_push_action(source_res, push_res)
        policy.steps_taken += 1
        return policy

    return _generator


def _random_push_preload_policy_generator(push_weight: Optional[float] = None) -> Callable[[List[PushGroup]], Policy]:
    dist = {ResourceType.SCRIPT: 32, ResourceType.CSS: 32, ResourceType.IMAGE: 24, ResourceType.FONT: 12}

    def _choose_with_dist(groups, distribution):
        subdist = sorted([(k, distribution[k]) for k in groups if groups[k]])
        sorted_groups = sorted([(k, v) for (k, v) in groups.items() if v])
        g, random_group = random.choices(sorted_groups, weights=[s[1] for s in subdist])[0]
        r = random.randrange(0, len(random_group))
        return g, r, random_group[r]

    def _generator(push_groups: List[PushGroup]) -> Policy:
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
    url: Optional[str],
    manifest: Optional[str],
    iterations: int,
    policy_generator: Callable[[List[PushGroup]], Policy],
    bandwidth: Optional[int],
    latency: Optional[int],
    cpu_slowdown: Optional[int],
    only_simulator: Optional[bool],
):
    default_client_env = get_default_client_environment()
    client_env = get_client_environment_from_parameters(
        bandwidth or default_client_env.bandwidth,
        latency or default_client_env.latency,
        cpu_slowdown or default_client_env.cpu_slowdown,
    )

    if not only_simulator:
        log.info("calculating page load time", url=url)
        with tempfile.TemporaryDirectory() as record_dir:
            if not manifest:
                # this is to work around the fact that mahimahi needs an empty directory
                # so we use TemporaryDirectory to get a unique name for a directory and
                # then delete it. After mahimahi runs and create the dir, then TemporaryDirectory
                # can delete it as normal
                os.rmdir(record_dir)

                config = get_config(EnvironmentConfig(replay_dir=record_dir, request_url=url))
                log.debug("recording webpage in Mahimahi", record_dir=record_dir)
                record_webpage(url, record_dir, config)
            else:
                config = get_config(EnvironmentConfig.load_file(manifest))
                log.debug("using recorded webpage", record_dir=config.env_config.replay_dir)

            plt, res_list, push_groups, push_plts, policies = _get_results_in_replay_server(
                config, client_env, iterations, policy_generator, capture_default=bool(bandwidth or latency)
            )

            env_config = EnvironmentConfig(
                replay_dir=config.env_config.replay_dir,
                request_url=config.env_config.request_url,
                push_groups=push_groups,
                har_resources=res_list,
            )

    else:
        env_config = EnvironmentConfig.load_file(manifest)
        policies = [policy_generator(env_config.push_groups) for _ in range(iterations)]

    log.debug("running simulator...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env)
    push_sim_plts = [sim.simulate_load_time(client_env, policy) for policy in policies]

    if not only_simulator:
        log.info("real page load time", page_load_time=plt)
        log.info("real push page load times", page_load_time=push_plts)
    log.info("simulated page load time", page_load_time=round(sim_plt, 3))
    log.info("simulated push page load time", page_load_time=[round(plt, 3) for plt in push_sim_plts])


def _get_results_in_replay_server(
    config: Config,
    client_env: ClientEnvironment,
    iterations: int,
    policy_generator: Callable[[List[PushGroup]], Policy],
    capture_default: bool = False,
):
    log.debug("capturing median PLT in mahimahi with given environment")
    orig_plt, res_list, push_groups, *_ = get_page_load_time_in_replay_server(
        config.env_config.request_url, client_env, config
    )

    # If the user passed in a custom environment, we want to use the PLT from that environment
    # but we want to use the HAR from the default page load to run in the simulator. This is to
    # allow the simulator to simulate the custom environment on top of the default environment
    # and to prevent conflating environments
    if capture_default:
        default_client_env = get_default_client_environment()
        log.debug("capturing HAR in mahimahi for simulator in default environment")
        default_har = capture_har_in_replay_server(config.env_config.request_url, config, default_client_env)
        res_list = har_entries_to_resources(default_har)
        push_groups = resource_list_to_push_groups(res_list)

    plts = []
    policies = []

    for _ in range(iterations):
        policy = policy_generator(push_groups)
        policies.append(policy)

        log.debug("getting HAR in mahimahi with policy:")
        log.debug(json.dumps(policy.as_dict, indent=4))
        plt, *_ = get_page_load_time_in_replay_server(config.env_config.request_url, client_env, config, policy)
        plts.append(plt)

    return orig_plt, res_list, push_groups, plts, policies
