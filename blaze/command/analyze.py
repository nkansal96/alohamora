""" Implements the commands for analyzing training progress """
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


@command.argument("url", help="The URL to analyze the page load time for")
@command.command
def page_load_time(args):
    """
    Captures a webpage and calculates the median page load time for a given website
    in a fast, no-latency Mahimahi shell. Then simulates the load based on profiling
    the page in the same Mahimahi shell.
    """
    log.info("calculating page load time", url=args.url)
    client_env = get_default_client_environment()

    with tempfile.TemporaryDirectory() as record_dir:
        config = get_config(EnvironmentConfig(replay_dir=record_dir, request_url=args.url))
        log.info("recording webpage in Mahimahi")
        record_webpage(args.url, record_dir, config)

        log.info("recording page execution in Mahimahi")
        log.debug("using client environment", **client_env._asdict())
        har = capture_har_in_mahimahi(args.url, config, client_env)
        res_list = har_entries_to_resources(har)
        push_groups = resource_list_to_push_groups(res_list)

    env_config = EnvironmentConfig(replay_dir="", request_url=args.url, push_groups=push_groups, har_resources=res_list)

    log.info("simulating page load time...")
    sim = Simulator(env_config)
    sim_plt = sim.simulate_load_time(client_env)

    log.info("real page load time", page_load_time=har.page_load_time_ms)
    log.info("simulated page load time", page_load_time=sim_plt)
