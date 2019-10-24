import subprocess
from typing import Dict


class DNSServer:
    def __init__(self, host_ip_map: Dict[str, str]):
        self.host_ip_map = host_ip_map
        self.proc = None

    def __enter__(self):
        args = ["-k", "-R"]
        for host, ip in self.host_ip_map.items():
            args.extend(["-A", f"/{host}/{ip}"])

        self.proc = subprocess.Popen(["dnsmasq", *args])

        # If wait lasts for more than 2 seconds, a TimeoutError will be raised, which is okay since it
        # means that dnsmasq is running successfully. If it finishes sooner, it means it crashed and
        # we should raise an exception
        try:
            self.proc.wait(2)
            raise RuntimeError("dnsmasq exited unsuccessfully")
        except TimeoutError:
            pass

    def __exit__(self, exception_type, exception_value, traceback):
        self.proc.kill()
        self.proc.wait()
