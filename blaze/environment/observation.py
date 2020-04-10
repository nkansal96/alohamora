"""
This module defines classes and methods related to creating the observation space
and generating observations based on some training state
"""

from typing import List, Set

import gym
import numpy as np

from blaze.action import Policy
from blaze.config.client import NetworkSpeed, NetworkType, DeviceSpeed, ClientEnvironment
from blaze.config.environment import PushGroup, ResourceType

MAX_RESOURCES = 200
MAX_DOMAINS = 200
MAX_KBYTES = 10000


def get_observation_space():
    """
    Returns the default observation space -- a description of valid observations that
    can be made from the environment. It encompasses client information, resources available
    to push, and the resources that are being pushed according to the current push policy
    """
    resource_space = gym.spaces.MultiDiscrete(
        [
            # 0 for disabled, 1 for enabled
            2,
            # 0 for not cached, 1 for cached
            2,
            # the push group (domain) this object is part of
            MAX_DOMAINS,
            # the source id (the position of this object relative to the domain) of this object
            MAX_RESOURCES,
            # the order (position of this object relative to the top of the page load) of this object, offset by 1
            MAX_RESOURCES + 1,
            # the initiator (order, offset by 1, of the object that requested this one)
            MAX_RESOURCES + 1,
            # the resource type
            len(ResourceType),
            # the size in kilobytes
            MAX_KBYTES,
            # the source ID of the resource that pushed this one, offset by 1 so that 0 indicates not pushed
            MAX_RESOURCES + 1,
            # the order of the resource that preloaded this one, offset by 1 so that 0 indicates not preloaded
            MAX_RESOURCES + 1,
        ]
    )
    return gym.spaces.Dict(
        {
            "client": gym.spaces.Dict(
                {
                    "network_type": gym.spaces.Discrete(len(NetworkType)),
                    "network_speed": gym.spaces.Discrete(len(NetworkSpeed)),
                    "device_speed": gym.spaces.Discrete(len(DeviceSpeed)),
                    "bandwidth_mbps": gym.spaces.Discrete(100),
                    "latency_ms": gym.spaces.Discrete(1000),
                    "loss": gym.spaces.Box(low=0, high=1, shape=(1,)),
                }
            ),
            "resources": gym.spaces.Dict({str(i): resource_space for i in range(MAX_RESOURCES)}),
        }
    )


def get_observation(
    client_environment: ClientEnvironment, push_groups: List[PushGroup], policy: Policy, cached_urls: Set[str]
):
    """
    Given the environment, list of pushable resources, and the current push policy,
    return an observation
    """
    # Encode the push groups
    encoded_resources = {str(i): np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) for i in range(MAX_RESOURCES)}

    for group in push_groups:
        for res in group.resources:
            # for some reason, sometimes res.type is in int instead of a ResourceType
            res_type = res.type.value if isinstance(res.type, ResourceType) else res.type
            res_size_kb = min(MAX_KBYTES - 1, res.size // 1000)
            cached = 1 if res.url in cached_urls else 0
            encoded_resources[str(res.order)] = np.array(
                [1, cached, group.id, res.source_id, res.order + 1, res.initiator + 1, res_type, res_size_kb, 0, 0]
            )

    for (source, push) in policy.observable_push:
        for push_res in push:
            # note that the pushed-from field is offset by 1, so that 0 indictates not pushed
            encoded_resources[str(push_res.order)][-2] = source.source_id + 1

    for (source, preload) in policy.observable_preload:
        for preload_res in preload:
            # note that the preloaded-from field is offset by 1, so that 0 indictates not pushed
            encoded_resources[str(preload_res.order)][-1] = source.order + 1

    return {
        "client": {
            "network_speed": client_environment.network_speed.value,
            "network_type": client_environment.network_type.value,
            "device_speed": client_environment.device_speed.value,
            "bandwidth_mbps": client_environment.bandwidth // 1000,
            "latency_ms": 10 * (client_environment.latency // 10),
            "loss": np.array([client_environment.loss]),
        },
        "resources": encoded_resources,
    }
