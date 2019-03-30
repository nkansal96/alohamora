""" Describes types used to configure client emulation """

import enum
import random
from typing import NamedTuple

class NetworkType(enum.IntEnum):
  """ NetworkType defines the type of network the client is accessing the page over """
  TYPE_WIFI = 0
  TYPE_LTE = 1
  TYPE_4G = 2
  TYPE_3G = 3

class NetworkBandwidth(enum.IntEnum):
  """ NetworkBandwidth defines the type of downlink bandwidth the client supports """
  BANDWIDTH_ULTRA_HIGH = 0
  BANDWIDTH_HIGH = 1
  BANDWIDTH_MED	= 2
  BANDWIDTH_LOW	= 3
  BANDWIDTH_ULTRA_LOW = 4

class NetworkLatency(enum.IntEnum):
  """ NetworkLatency defines the average latency between the client and the server """
  LATENCY_ULTRA_LOW = 0
  LATENCY_LOW	= 1
  LATENCY_MED	= 2
  LATENCY_HIGH = 3
  LATENCY_ULTRA_HIGH = 4

class DeviceSpeed(enum.IntEnum):
  """ DeviceSpeed defines the processing capabilities of the client """
  DESKTOP	= 0
  FAST_MOBILE = 1
  SLOW_MOBILE = 2

class ClientEnvironment(NamedTuple):
  """ ClientEnvironment consists of a network type, bandwidth, and latency, and device speed """
  network_type: NetworkType
  network_bandwidth: NetworkBandwidth
  network_latency: NetworkLatency
  device_speed: DeviceSpeed

def get_random_client_environment():
  """ Returns a random ClientEnvironment """
  return ClientEnvironment(
    network_type=random.choice(list(NetworkType)),
    network_bandwidth=random.choice(list(NetworkBandwidth)),
    network_latency=random.choice(list(NetworkLatency)),
    device_speed=random.choice(list(DeviceSpeed)),
  )
