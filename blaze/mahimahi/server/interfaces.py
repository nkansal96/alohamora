import subprocess
from typing import List

from blaze.logger import logger


def generate_ips(num_ips: int):
    return [f"10.0.{1 + (i // 255)}.{1 + (i % 255)}" for i in range(num_ips)]


class Interfaces:
    def __init__(self, hosts: List[str]):
        self.hosts = hosts
        self.log = logger.with_namespace("interface")

    @property
    def ip_addresses(self):
        return generate_ips(len(self.hosts))

    @property
    def mapping(self):
        return dict(zip(self.hosts, self.ip_addresses))

    def create_interfaces(self):
        for ip in self.ip_addresses:
            self.log.debug("creating interface", device="lo", address=ip)
            subprocess.run(["ip", "addr", "add", f"{ip}/32", "dev", "lo"], check=True)

    def delete_interfaces(self):
        for ip in self.ip_addresses:
            self.log.debug("deleting interface", device="lo", address=ip)
            subprocess.run(["ip", "addr", "del", f"{ip}/32", "dev", "lo"])

    def __enter__(self):
        try:
            self.create_interfaces()
        except subprocess.CalledProcessError:
            self.delete_interfaces()
            raise

    def __exit__(self, exception_type, exception_value, traceback):
        self.delete_interfaces()
