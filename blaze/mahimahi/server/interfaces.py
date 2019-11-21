""" This module defines Interfaces, which manages the virtual IPs created on the system for some given hosts """

import subprocess
import sys
from typing import List

from blaze.logger import logger


def generate_ips(num_ips: int, offset: int = 0) -> List[str]:
    """
    Generates a list of unique IP addresses (sequential starting from 10.0.1.1) for the
    given number of IPs starting at the given offset
    :param num_ips: The numer of IPs to generate
    :param offset: The offset to start generating from
    :return: A list of IP addresses
    """
    return [f"10.0.{1 + (i // 255)}.{1 + (i % 255)}" for i in range(offset, offset + num_ips)]


class Interfaces:
    """
    Interfaces implements a context manager that creates and deletes IP addresses corresponding
    to the given hosts.
    """

    def __init__(self, hosts: List[str]):
        """
        :param hosts: The hosts to manage IP addresses for
        """
        self.hosts = hosts
        self.log = logger.with_namespace("interface")

    @property
    def ip_addresses(self):
        """
        :return: the IP addresses required for the given hosts
        """
        return generate_ips(len(self.hosts))

    @property
    def mapping(self):
        """
        :return: A mapping of host-ip for the given hosts
        """
        return dict(zip(self.hosts, self.ip_addresses))

    def create_interfaces(self):
        """
        Creates the virtual IPs on lo corresponding to the given hosts
        """
        for ip_addr in self.ip_addresses:
            self.log.debug("creating interface", device="lo", address=ip_addr)
            subprocess.run(["ip", "addr", "add", f"{ip_addr}/32", "dev", "lo"], check=True, stdout=sys.stderr, stderr=sys.stderr)

    def delete_interfaces(self):
        """
        Deletes the created virtual IPs on lo
        """
        for ip_addr in self.ip_addresses:
            self.log.debug("deleting interface", device="lo", address=ip_addr)
            subprocess.run(["ip", "addr", "del", f"{ip_addr}/32", "dev", "lo"], stdout=sys.stderr, stderr=sys.stderr)

    def __enter__(self):
        try:
            self.create_interfaces()
        except subprocess.CalledProcessError:
            self.delete_interfaces()
            raise

    def __exit__(self, exception_type, exception_value, traceback):
        self.delete_interfaces()
