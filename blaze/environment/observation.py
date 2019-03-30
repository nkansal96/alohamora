"""
This module defines classes and methods related to creating the observation space
and generating observations based on some training state
"""

from typing import List

import gym
import numpy as np

from blaze.action import Policy
from blaze.config.client import NetworkType, NetworkBandwidth, NetworkLatency, DeviceSpeed, ClientEnvironment
from blaze.config.train import PushGroup, ResourceType

MAX_PUSH_GROUPS = 100
MAX_RESOURCES = 400
MAX_BYTES = 10000000

def get_observation_space():
  """
  Returns the default observation space -- a description of valid observations that
  can be made from the environment. It encompasses client information, resources available
  to push, and the resources that are being pushed according to the current push policy
  """
  enabled_space = gym.spaces.Discrete(2)
  type_space = gym.spaces.Discrete(len(ResourceType))
  size_space = gym.spaces.Discrete(MAX_BYTES)
  push_from_space = gym.spaces.Discrete(MAX_RESOURCES + 1)
  push_group = gym.spaces.Dict({
    str(j): gym.spaces.Dict({
      'enabled': enabled_space,
      'type': type_space,
      'size': size_space,
      'push_from': push_from_space,
    }) for j in range(MAX_RESOURCES)
  })
  return gym.spaces.Dict({
    'client': gym.spaces.Dict({
      'network_type': gym.spaces.Discrete(len(NetworkType)),
      'network_bandwidth': gym.spaces.Discrete(len(NetworkBandwidth)),
      'network_latency': gym.spaces.Discrete(len(NetworkLatency)),
      'device_speed': gym.spaces.Discrete(len(DeviceSpeed)),
    }),
    'push_groups': gym.spaces.Dict({
      str(i): push_group for i in range(MAX_PUSH_GROUPS)
    }),
  })

def get_observation(client_environment: ClientEnvironment, push_groups: List[PushGroup], policy: Policy):
  """
  Given the environment, list of pushable resources, and the current push policy,
  return an observation
  """
  # Encode the push groups
  encoded_push_groups = {
    str(i): {
      str(j): {'enabled': 0, 'type': 0, 'size': 0, 'push_from': 0} for j in range(MAX_RESOURCES)
    } for i in range(MAX_PUSH_GROUPS)
  }

  for g, group in enumerate(push_groups):
    for s, res in enumerate(group.resources):
      encoded_push_groups[str(g)][str(s)] = {'enabled': 1, 'type': res.type.value, 'size': res.size, 'push_from': 0}

  for (source, push) in policy:
    for push_res in push:
      encoded_push_groups[str(source.group_id)][str(push_res.source_id)]['push_from'] = source.source_id

  return {
    'client': {
      'network_type': client_environment.network_type.value,
      'network_bandwidth': client_environment.network_bandwidth.value,
      'network_latency': client_environment.network_latency.value,
      'device_speed': client_environment.device_speed.value,
    },
    'push_groups': encoded_push_groups,
  }
