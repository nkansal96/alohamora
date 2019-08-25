""" Implements the commands for analyzing training progress """
import json
import os
import random
import tempfile
from typing import Callable, List, Optional

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_client_environment_from_parameters, get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig, PushGroup, ResourceType
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import capture_har_in_mahimahi, record_webpage, get_page_load_time_in_mahimahi
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups
from . import command


@command.argument("url", nargs="?", help="The URL to analyze the page load time for")
@command.argument("--policy_type", help="The test type to run", choices=["simple", "random"])
@command.argument(
    "--random_chance",
    help="Probability of pushing a particular resource (only used for --policy_type=random)",
    type=float,
    default=0.25,
)
@command.argument("--iterations", help="Number of trials", type=int, default=1)
@command.argument("--bandwidth", help="Link bandwidth to simulate (kbps)", type=int, default=None)
@command.argument("--latency", help="Link RTT to simulate (ms)", type=int, default=None)
@command.command
def test_push(args):
    """
    Runs a pre-defined test on the given webpage
    """
    if args.policy_type == "simple":
        _test_push(args.url, 1, _simple_push_policy_generator(), args.bandwidth, args.latency)
    if args.policy_type == "random":
        _test_push(args.url, args.iterations, _random_push_policy_generator(args.random_chance), args.bandwidth, args.latency)


def _simple_push_policy_generator() -> Callable[[List[PushGroup]], Policy]:
    def _simple_push_policy(push_groups: List[PushGroup]) -> Policy:
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
        policy = Policy(ActionSpace([]))
        policy.add_default_action(source_res, push_res)
        return policy

    return _simple_push_policy


def _random_push_policy_generator(chance: float) -> Callable[[List[PushGroup]], Policy]:
    def _random_push_policy(push_groups: List[PushGroup]) -> Policy:
        policy = Policy(ActionSpace([]))
        for group in push_groups:
            for push in range(1, len(group.resources)):
                if random.random() > chance:
                    continue
                source = random.randint(0, push - 1)
                policy.add_default_action(group.resources[source], group.resources[push])

        return policy

    return _random_push_policy


def _test_push(
    url: str, iterations: int, policy_generator: Callable[[List[PushGroup]], Policy], bandwidth: Optional[int], latency: Optional[int]
):
    default_client_env = get_default_client_environment()
    client_env = get_client_environment_from_parameters(
        bandwidth or default_client_env.bandwidth, latency or default_client_env.latency, 1
    )

    log.info("calculating page load time", url=url)
    with tempfile.TemporaryDirectory() as record_dir:
        # this is to work around the fact that mahimahi needs an empty directory
        # so we use TemporaryDirectory to get a unique name for a directory and
        # then delete it. After mahimahi runs and create the dir, then TemporaryDirectory
        # can delete it as normal
        os.rmdir(record_dir)

        config = get_config(EnvironmentConfig(replay_dir=record_dir, request_url=url))
        log.debug("recording webpage in Mahimahi", record_dir=record_dir)
        record_webpage(url, record_dir, config)

        log.debug("capturing median PLT in mahimahi with given environment")
        plt, res_list, push_groups = get_page_load_time_in_mahimahi(config.env_config.request_url, client_env, config)

        # If the user passed in a custom environment, we want to use the PLT from that environment
        # but we want to use the HAR from the default page load to run in the simulator. This is to
        # allow the simulator to simulate the custom environment on top of the default environment
        # and to prevent conflating environments
        if bandwidth or latency:
            log.debug("capturing HAR in mahimahi for simulator in default environment")
            default_har = capture_har_in_mahimahi(url, config, default_client_env)
            res_list = har_entries_to_resources(default_har)
            push_groups = resource_list_to_push_groups(res_list)

        push_plts = []
        push_policies = []

        for _ in range(iterations):
            policy = policy_generator(push_groups)
            push_policies.append(policy)

            log.debug("getting HAR in mahimahi with push policy:")
            log.debug(json.dumps(policy.as_dict, indent=4))
            push_plt, *_ = get_page_load_time_in_mahimahi(config.env_config.request_url, client_env, config, policy)
            push_plts.append(push_plt)

        env_config = EnvironmentConfig(
            replay_dir=record_dir, request_url=url, push_groups=push_groups, har_resources=res_list
        )

    log.debug("running simulator...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env)
    push_sim_plts = []

    for policy in push_policies:
        sim = Simulator(env_config)
        push_sim_plts.append(sim.simulate_load_time(client_env, policy))

    log.info("real page load time", page_load_time=plt)
    log.info("real push page load times", page_load_time=push_plts)
    log.info("simulated page load time", page_load_time=sim_plt)
    log.info("simulated push page load time", page_load_time=push_sim_plts)
