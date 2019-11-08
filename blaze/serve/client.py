""" Defines a test client that queries the gRPC server to get a policy """
import json
from typing import List

import grpc

from blaze.action import Policy
from blaze.config.client import NetworkType, DeviceSpeed
from blaze.config.environment import EnvironmentConfig
from blaze.config.environment import Resource
from blaze.proto import policy_service_pb2
from blaze.proto import policy_service_pb2_grpc


class Client:
    """
    A gRPC client that connects to the policy service and queries it for a policy
    """

    def __init__(self, channel: grpc.Channel):
        self.channel = channel
        self.stub = policy_service_pb2_grpc.PolicyServiceStub(channel)

    def get_policy(
        self,
        url: str,
        network_type: NetworkType,
        device_speed: DeviceSpeed,
        manifest: EnvironmentConfig,
    ) -> Policy:
        """ Queries the policy service for a push policy for the given configuration """
        page = policy_service_pb2.Page(
            url=url,
            network_type=network_type.value,
            device_speed=device_speed.value,
            manifest=manifest.serialize(),
        )

        policy_res = self.stub.GetPolicy(page)
        return Policy.from_dict(json.loads(policy_res.policy))
