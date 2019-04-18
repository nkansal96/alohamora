"""
This module defines classes and methods related to creating the observation space
and generating observations based on some training state
"""

from typing import List

import gym
import numpy as np

from blaze.action import Policy
from blaze.config.client import NetworkType, DeviceSpeed, ClientEnvironment
from blaze.config.environment import PushGroup, ResourceType

MAX_RESOURCES = 200
MAX_KBYTES = 10000

def get_observation_space():
  """
  Returns the default observation space -- a description of valid observations that
  can be made from the environment. It encompasses client information, resources available
  to push, and the resources that are being pushed according to the current push policy
  """
  resource_space = gym.spaces.MultiDiscrete([
    # 0 for disabled, 1 for enabled
    2,
    # the resource type
    len(ResourceType),
    # the size in kilobytes
    MAX_KBYTES,
    # the resource that pushed this one
    MAX_RESOURCES
  ])
  return gym.spaces.Dict({
    'client': gym.spaces.Dict({
      'network_type': gym.spaces.Discrete(len(NetworkType)),
      'device_speed': gym.spaces.Discrete(len(DeviceSpeed)),
    }),
    'resources': gym.spaces.Dict({
      str(i): resource_space for i in range(MAX_RESOURCES)
    }),
  })

def get_observation(client_environment: ClientEnvironment, push_groups: List[PushGroup], policy: Policy):
  """
  Given the environment, list of pushable resources, and the current push policy,
  return an observation
  """
  # Encode the push groups
  encoded_resources = {
    str(i): np.array([0, 0, 0, 0]) for i in range(MAX_RESOURCES)
  }

  for group in push_groups:
    for res in group.resources:
      encoded_resources[str(res.order)] = np.array([1, res.type.value, res.size//1000, 0])

  for (source, push) in policy:
    for push_res in push:
      encoded_resources[str(push_res.order)][3] = source.order

  return {
    'client': {
      'network_type': client_environment.network_type.value,
      'device_speed': client_environment.device_speed.value,
    },
    'resources': encoded_resources,
  }
