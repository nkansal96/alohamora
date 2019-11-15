""" This module implements methods interacting with Chrome DevTools """
import json
import os
import subprocess
import sys
import tempfile
from typing import Optional

from blaze.action.policy import Policy
from blaze.config.client import ClientEnvironment
from blaze.config.config import Config
from blaze.logger import logger
from blaze.mahimahi import MahiMahiConfig

from .har import har_from_json, Har


def capture_har(url: str, config: Config, output_filepath: Optional[str] = None) -> Har:
    """
    capture_har spawns a headless chrome instance and connects to its remote debugger
    in order to extract the HAR file generated by loading the given URL.
    """
    log = logger.with_namespace("capture_har")

    # configure the HAR capturer
    har_capture_cmd = [config.chrome_har_capturer_bin, "--url", url]
    if output_filepath:
        har_capture_cmd.extend(["--output-file", output_filepath])

    # spawn the HAR capturer process
    log.debug("spawning har capturer", url=url)
    har_capture_proc = subprocess.run(har_capture_cmd, stdout=subprocess.PIPE)
    har_capture_proc.check_returncode()
    if output_filepath:
        with open(output_filepath, "r") as output_file:
            return har_from_json(output_file.read())
    return har_from_json(har_capture_proc.stdout)


def capture_har_in_mahimahi(
    url: str, config: Config, client_env: ClientEnvironment, policy: Optional[Policy] = None
) -> Har:
    """
    capture_har spawns a headless chrome instance and connects to its remote debugger
    in order to extract the HAR file generated by loading the given URL. The har capturer
    is launched inside a replay shell using the specified Mahimahi config, which means
    that the webpage needs to have been recorded before calling this method
    """
    log = logger.with_namespace("capture_har_in_mahimahi")

    if not config.env_config or not config.env_config.replay_dir:
        raise ValueError("replay_dir must be specified")

    policy = policy or Policy.from_dict({})
    mahimahi_config = MahiMahiConfig(config=config, policy=policy, client_environment=client_env)

    with tempfile.TemporaryDirectory() as temp_dir:
        policy_file = os.path.join(temp_dir, "policy.json")
        output_file = os.path.join(temp_dir, "har.json")
        trace_file = os.path.join(temp_dir, "trace_file")

        with open(policy_file, "w") as f:
            log.debug("writing push policy file", policy_file=policy_file)
            f.write(json.dumps(policy.as_dict))
        with open(trace_file, "w") as f:
            log.debug("writing trace file", trace_file=trace_file)
            f.write(mahimahi_config.formatted_trace_file)

        # configure the HAR capturer
        cmd = mahimahi_config.har_capture_cmd(
            share_dir=temp_dir,
            har_output_file_name="har.json",
            policy_file_name="policy.json",
            link_trace_file_name="trace_file",
            capture_url=url,
        )

        # spawn the HAR capturer process
        log.debug("spawning har capturer", url=url, cmd=cmd)
        har_capture_proc = subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
        har_capture_proc.check_returncode()

        with open(output_file, "r") as f:
            return har_from_json(f.read())
