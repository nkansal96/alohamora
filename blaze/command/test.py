""" Implements the commands for analyzing training progress """
import collections
import json
import os
import random
import tempfile
from typing import Callable, List, Optional, Tuple

from blaze.action import Policy
from blaze.config.client import get_client_environment_from_parameters, get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig, PushGroup, ResourceType
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import capture_har_in_mahimahi, record_webpage, get_page_load_time_in_mahimahi
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups
from . import command


@command.argument(
    "--policy_type", help="The test type to run", choices=["simple", "random", "push_preload"], required=True
)
@command.argument(
    "--random_chance",
    help="Probability of pushing a particular resource (only used for --policy_type=random)",
    type=float,
    default=None,
)
@command.argument("--from_manifest", required=True, help="The training manifest file to use as input to the simulator")
@command.command
def random_push_policy(args):
    """
    Outputs a random push policy for the given recorded website
    """
    log.info("generating a random policy", policy_type=args.policy_type, random_chance=args.random_chance or "auto")
    env_config = EnvironmentConfig.load_file(args.from_manifest)

    push_policy = None
    preload_policy = None
    if args.policy_type == "simple":
        push_policy, preload_policy = _simple_push_policy_generator()(env_config.push_groups)
    if args.policy_type == "random":
        push_policy, preload_policy = _random_push_policy_generator(args.random_chance)(env_config.push_groups)
    if args.policy_type == "push_preload":
        push_policy, preload_policy = _random_push_preload_policy_generator()(env_config.push_groups)

    policy = {}
    if push_policy:
        policy["push"] = push_policy.as_dict
    if preload_policy:
        policy["preload"] = preload_policy.as_dict
    print(json.dumps(policy, indent=4))


@command.argument("url", nargs="?", help="The URL to analyze the page load time for")
@command.argument("--from_manifest", help="The training manifest file to use as input to the simulator")
@command.argument(
    "--only_simulator",
    action="store_true",
    help="Only evaluate the page load time on the simulator (must be loaded from manifest to use this)",
)
@command.argument(
    "--policy_type", help="The test type to run", choices=["simple", "random", "push_preload"], default="random"
)
@command.argument(
    "--random_chance",
    help="Probability of pushing a particular resource (only used for --policy_type=random). If not specified, the "
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

    policy_generator = None
    if args.policy_type == "simple":
        policy_generator = _simple_push_policy_generator()
    if args.policy_type == "random":
        policy_generator = _random_push_policy_generator(args.random_chance)
    if args.policy_type == "push_preload":
        policy_generator = _random_push_preload_policy_generator()

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


def _simple_push_policy_generator() -> Callable[[List[PushGroup]], Tuple[Policy, Policy]]:
    def _generator(push_groups: List[PushGroup]) -> Tuple[Policy, Policy]:
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
        policy = Policy.from_dict({})
        policy.add_default_action(source_res, push_res)
        policy.steps_taken += 1
        return policy, Policy.from_dict({})

    return _generator


def _random_push_policy_generator(chance: Optional[float] = None) -> Callable[[List[PushGroup]], Tuple[Policy, Policy]]:
    def _generator(push_groups: List[PushGroup]) -> Tuple[Policy, Policy]:
        _chance = chance
        if not _chance:
            _chance = random.random()

        policy = Policy.from_dict({})
        for group in push_groups:
            for push in range(1, len(group.resources)):
                if random.random() > _chance:
                    continue
                source = random.randint(0, push - 1)
                policy.add_default_action(group.resources[source], group.resources[push])
                policy.steps_taken += 1

        return policy, Policy.from_dict({})

    return _generator


def _random_push_preload_policy_generator() -> Callable[[List[PushGroup]], Tuple[Policy, Policy]]:
    dist = {ResourceType.SCRIPT: 32, ResourceType.CSS: 32, ResourceType.IMAGE: 24, ResourceType.FONT: 12}

    def _choose_with_dist(groups, distribution):
        subdist = sorted([(k, distribution[k]) for k in groups if groups[k]])
        sorted_groups = sorted([(k, v) for (k, v) in groups.items() if v])
        g, random_group = random.choices(sorted_groups, weights=[s[1] for s in subdist])[0]
        r = random.randrange(0, len(random_group))
        return g, r, random_group[r]

    def _generator(push_groups: List[PushGroup]) -> Tuple[Policy, Policy]:
        # Collect all resources and group them by type
        all_resources = sorted([res for group in push_groups for res in group.resources], key=lambda res: res.order)
        res_by_type = collections.defaultdict(list)
        for res in all_resources:
            # Only consider objects in the push resource type distribution
            if res.type in dist:
                res_by_type[res.type].append(res)

        # choose the number of resources to push/preload
        n = random.randint(1, len(all_resources))
        # choose the weight factor between push and preload
        weight = random.random()

        # Choose n resources based on the resource type distribution without replacement
        log.debug("generating push-preload policy", num_resources=len(all_resources), total_size=n, push_weight=weight)
        res = []
        for _ in range(n):
            g, r, s = _choose_with_dist(res_by_type, dist)
            res_by_type[g].pop(r)
            res.append(s)

        push_policy = Policy.from_dict({})
        preload_policy = Policy.from_dict({})

        for r in res:
            push = random.random() < weight
            if push:
                source = random.randint(0, r.source_id)
                push_policy.add_default_action(push_groups[r.group_id].resources[source], r)
                push_policy.steps_taken += 1
            else:
                source = random.randint(0, r.order)
                preload_policy.add_default_action(all_resources[source], r)
                preload_policy.steps_taken += 1

        return push_policy, preload_policy

    return _generator


def _test_push(
    url: Optional[str],
    manifest: Optional[str],
    iterations: int,
    policy_generator: Callable[[List[PushGroup]], Tuple[Policy, Policy]],
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

            plt, res_list, push_groups, push_plts, push_policies = _get_results_in_mahimahi(
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
        push_policies = [policy_generator(env_config.push_groups)[0] for _ in range(iterations)]

    log.debug("running simulator...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env)
    push_sim_plts = [sim.simulate_load_time(client_env, policy) for policy in push_policies]

    if not only_simulator:
        log.info("real page load time", page_load_time=plt)
        log.info("real push page load times", page_load_time=push_plts)
    log.info("simulated page load time", page_load_time=round(sim_plt, 3))
    log.info("simulated push page load time", page_load_time=[round(plt, 3) for plt in push_sim_plts])


def _get_results_in_mahimahi(config, client_env, iterations, policy_generator, capture_default=False):
    log.debug("capturing median PLT in mahimahi with given environment")
    plt, res_list, push_groups = get_page_load_time_in_mahimahi(config.env_config.request_url, client_env, config)

    # If the user passed in a custom environment, we want to use the PLT from that environment
    # but we want to use the HAR from the default page load to run in the simulator. This is to
    # allow the simulator to simulate the custom environment on top of the default environment
    # and to prevent conflating environments
    if capture_default:
        default_client_env = get_default_client_environment()
        log.debug("capturing HAR in mahimahi for simulator in default environment")
        default_har = capture_har_in_mahimahi(config.env_config.request_url, config, default_client_env)
        res_list = har_entries_to_resources(default_har)
        push_groups = resource_list_to_push_groups(res_list)

    push_plts = []
    push_policies = []

    for _ in range(iterations):
        push_policy, preload_policy = policy_generator(push_groups)
        push_policies.append(push_policy)

        log.debug("getting HAR in mahimahi with push policy:")
        log.debug(json.dumps(push_policy.as_dict, indent=4))
        log.debug("preload policy:")
        log.debug(json.dumps(preload_policy.as_dict, indent=4))
        push_plt, *_ = get_page_load_time_in_mahimahi(
            config.env_config.request_url, client_env, config, push_policy, preload_policy
        )
        push_plts.append(push_plt)

    return plt, res_list, push_groups, push_plts, push_policies
