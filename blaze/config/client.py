from typing import List
import collections

import collections
import enum

class NetworkType(enum.IntEnum):
    TYPE_WIFI = 0
    TYPE_LTE  = 1
    TYPE_4G   = 2
    TYPE_3G   = 3

class NetworkBandwidth(enum.IntEnum):
    BANDWIDTH_ULTRA_HIGH = 0
    BANDWIDTH_HIGH       = 1
    BANDWIDTH_MED        = 2
    BANDWIDTH_LOW        = 3
    BANDWIDTH_ULTRA_LOW  = 4

class NetworkLatency(enum.IntEnum):
    LATENCY_ULTRA_LOW  = 0
    LATENCY_LOW        = 1
    LATENCY_MED        = 2
    LATENCY_HIGH       = 3
    LATENCY_ULTRA_HIGH = 4

class DeviceSpeed(enum.IntEnum):
    DESKTOP     = 0
    FAST_MOBILE = 1
    SLOW_MOBILE = 2

class ClientEnvironment(object):
  def __init__(self,
    network_type: NetworkType, network_bandwidth: NetworkBandwidth,
    network_latency: NetworkLatency, device_speed: DeviceSpeed):
    self.network_type = network_type
    self.network_bandwidth = network_bandwidth
    self.network_latency = network_latency
    self.device_speed = device_speed
