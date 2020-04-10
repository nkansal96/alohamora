""" Describes types used to configure client emulation """

import enum
import random
from typing import NamedTuple, Tuple


class NetworkType(enum.IntEnum):
    """ NetworkType defines the type of network the client is accessing the page over """

    WIRED = 0
    WIFI = 1
    LTE = 2
    UMTS = 3


class NetworkSpeed(enum.IntEnum):
    """ NetworkSpeed defines the overall speed of the network the client is accessing the page over """

    FAST = 0
    SLOW = 1


class DeviceSpeed(enum.IntEnum):
    """ DeviceSpeed defines the processing capabilities of the client """

    DESKTOP = 0
    FAST_MOBILE = 1
    SLOW_MOBILE = 2


class ClientEnvironment(NamedTuple):
    """ ClientEnvironment consists of a network type, bandwidth, and latency, and device speed """

    network_type: NetworkType
    device_speed: DeviceSpeed
    network_speed: NetworkSpeed
    bandwidth: int = 0
    latency: int = 0
    cpu_slowdown: int = 0
    loss: float = 0  # Should be between 0 and 1


def network_to_bandwidth_range(network_type: NetworkType, network_speed: NetworkSpeed) -> Tuple[int, int]:
    """ Returns the (low, high) bandwidth range in kbps for the given network type """
    network_bandwidth_map = {
        NetworkType.WIRED: {NetworkSpeed.FAST: (48000, 96000), NetworkSpeed.SLOW: (24000, 48000)},
        NetworkType.WIFI: {NetworkSpeed.FAST: (12000, 26000), NetworkSpeed.SLOW: (6000, 12000)},
        NetworkType.LTE: {NetworkSpeed.FAST: (12000, 26000), NetworkSpeed.SLOW: (6000, 12000)},
        NetworkType.UMTS: {NetworkSpeed.FAST: (6000, 12000), NetworkSpeed.SLOW: (1000, 6000)},
    }
    return network_bandwidth_map[network_type][network_speed]


def network_to_latency_range(network_type: NetworkType) -> Tuple[int, int]:
    """ Returns the (low, high) Round-trip latency range in ms for the given network type """
    network_latency_map = {
        NetworkType.WIRED: (2, 10),
        NetworkType.WIFI: (10, 40),
        NetworkType.LTE: (40, 100),
        NetworkType.UMTS: (60, 120),
    }
    return network_latency_map[network_type]


def device_speed_to_cpu_slowdown(device_speed: DeviceSpeed) -> int:
    """ Returns the CPU slowdown factor (for Chrome DevTools) for the given device speed """
    device_speed_map = {DeviceSpeed.DESKTOP: 1, DeviceSpeed.FAST_MOBILE: 2, DeviceSpeed.SLOW_MOBILE: 4}
    return device_speed_map[device_speed]


def get_random_client_environment():
    """ Returns a random ClientEnvironment """
    network_type = random.choice(list(NetworkType))
    network_speed = random.choice(list(NetworkSpeed))
    device_speed = random.choice(list(DeviceSpeed))
    bandwidth_range = network_to_bandwidth_range(network_type, network_speed)
    latency_range = network_to_latency_range(network_type)
    cpu_slowdown = device_speed_to_cpu_slowdown(device_speed)

    return ClientEnvironment(
        network_type=network_type,
        network_speed=network_speed,
        device_speed=device_speed,
        bandwidth=random.randrange(*bandwidth_range, 1000),
        latency=random.randrange(*latency_range, 2),
        cpu_slowdown=cpu_slowdown,
    )


def get_random_fast_lte_client_environment():
    """ Returns a random fast mobile LTE ClientEnvironment"""
    network_type = random.choice([NetworkType.LTE, NetworkType.WIFI])
    network_speed = NetworkSpeed.FAST
    device_speed = random.choice([DeviceSpeed.FAST_MOBILE, DeviceSpeed.SLOW_MOBILE, DeviceSpeed.DESKTOP])
    bandwidth_range = network_to_bandwidth_range(network_type, network_speed)
    latency_range = network_to_latency_range(network_type)
    cpu_slowdown = device_speed_to_cpu_slowdown(device_speed)
    return ClientEnvironment(
        network_type=network_type,
        network_speed=network_speed,
        device_speed=device_speed,
        bandwidth=random.randrange(*bandwidth_range, 1000),
        latency=random.randrange(*latency_range, 2),
        cpu_slowdown=cpu_slowdown,
    )


def get_fast_mobile_client_environment():
    """ Returns a ClientEnvironment with 40ms latency, 48 Mbps throughput, and no device slowdown """
    return ClientEnvironment(
        network_type=NetworkType.LTE,
        network_speed=NetworkSpeed.FAST,
        device_speed=DeviceSpeed.DESKTOP,
        bandwidth=24000,
        latency=20,
        cpu_slowdown=1,
    )


def get_default_client_environment():
    """ Returns a ClientEnvironment with 0ms latency and 96 Mbps throughput, no device slowdown """
    return ClientEnvironment(
        network_type=NetworkType.WIRED,
        network_speed=NetworkSpeed.FAST,
        device_speed=DeviceSpeed.DESKTOP,
        bandwidth=96000,
        latency=0,
        cpu_slowdown=1,
    )


def get_client_environment_from_parameters(bandwidth: int, latency: int, cpu_slowdown: int):
    """
    Returns a fully configured client environment for valid values of bandwidth, latency, and CPU slowdown
    """
    network_type, network_speed = next(
        (nt, ns)
        for nt in NetworkType
        for ns in NetworkSpeed
        if network_to_bandwidth_range(nt, ns)[0] <= bandwidth <= network_to_bandwidth_range(nt, ns)[1]
    )
    device_speed = next(ds for ds in DeviceSpeed if device_speed_to_cpu_slowdown(ds) == cpu_slowdown)
    return ClientEnvironment(
        network_type=network_type,
        network_speed=network_speed,
        device_speed=device_speed,
        bandwidth=bandwidth,
        latency=latency,
        cpu_slowdown=cpu_slowdown,
    )
