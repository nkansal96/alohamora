"""
This module defines the classes and methods used to configure Mahimahi shells
"""

from typing import List, Optional

from blaze.action import Policy
from blaze.config import Config
from blaze.config.client import ClientEnvironment
from .trace import format_trace_lines, trace_for_kbps


class MahiMahiConfig:
    """ MahiMahiConfig represents a configuration for some Mahimahi shells """

    def __init__(
        self, config: Config, *, policy: Optional[Policy] = None, client_environment: Optional[ClientEnvironment] = None
    ):
        self.config = config
        self.policy = policy
        self.client_environment = client_environment

    def har_capture_cmd(
        self,
        *,
        share_dir: str,
        har_output_file_name: str,
        policy_file_name: Optional[str] = None,
        link_trace_file_name: str = "",
        capture_url: str,
        user_data_dir: Optional[str] = None,
        extract_critical_requests: bool = False,
    ) -> List[str]:
        """
        Returns the full command to run that replays the configured folder with the given
        push policy and link trace name and stores output in the given output locations.

        :param share_dir: the directory to share to the container
        :param har_output_file_name: the file inside share_dir to write the HAR output to
        :param policy_file_name: the file inside share_dir to read the push/preload policy from (JSON formatted)
        :param link_trace_file_name: the file inside share_dir to read the link trace from (Mahimahi formatted). If not
                                     specified, no mm-link shell will be spawned.
        :param capture_url: The url to capture HAR for
        """
        return [
            "docker",
            "run",
            "--rm",
            "--privileged",
            "-v",
            f"{self.config.env_config.replay_dir}:/mnt/filestore",
            "-v",
            f"{share_dir}:/mnt/share",
            self.config.http2push_image,
            "--file-store-path",
            "/mnt/filestore",
            "--output-file",
            f"/mnt/share/{har_output_file_name}",
            *(["--policy-path", f"/mnt/share/{policy_file_name}"] if policy_file_name else []),
            *(["--link-trace-path", f"/mnt/share/{link_trace_file_name}"] if link_trace_file_name else []),
            *(["--link-latency-ms", str(self.client_environment.latency // 2)] if self.client_environment else []),
            *(["--cpu-slowdown", str(self.client_environment.cpu_slowdown)] if self.client_environment else []),
            *(["--user-data-dir", user_data_dir] if user_data_dir else []),
            *(["--extract-critical-requests"] if extract_critical_requests else []),
            "--url",
            capture_url,
        ]

    def si_capture_cmd(
        self,
        *,
        share_dir: str,
        si_output_file_name: str,
        policy_file_name: Optional[str] = None,
        link_trace_file_name: str = "",
        capture_url: str,
        user_data_dir: str,
    ) -> List[str]:
        har_cmd = self.har_capture_cmd(share_dir=share_dir, har_output_file_name=si_output_file_name, policy_file_name=policy_file_name, link_trace_file_name=link_trace_file_name, capture_url=capture_url, user_data_dir=user_data_dir, extract_critical_requests=False)
        har_cmd.append("--speed-index")
        return har_cmd

    def record_shell_with_cmd(self, save_dir: str, cmd: List[str]) -> List[str]:
        """
        Returns a command that can be run to start an optional link shell and web
        record shell with the given command
        """
        return [*self.record_cmd(save_dir), *cmd]

    def record_cmd(self, save_dir: str) -> List[str]:
        """ Returns the command to create a record shell with the given target directory """
        return ["mm-webrecord", save_dir]

    @property
    def formatted_trace_file(self):
        """
        Returns a string with a correctly formatted trace file for the bandwidth specified
        in the client environment
        """
        return format_trace_lines(trace_for_kbps(self.client_environment.bandwidth))
