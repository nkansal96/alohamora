""" Defines a test client that queries the gRPC server to get a policy """
import json
from typing import List

import grpc

from blaze.action import Policy
from blaze.config.client import NetworkType, DeviceSpeed
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
        resources: List[Resource],
        train_domain_globs: List[str],
    ) -> Policy:
        """ Queries the policy service for a push policy for the given configuration """
        page = policy_service_pb2.Page(
            url=url,
            network_type=network_type.value,
            device_speed=device_speed.value,
            train_domain_globs=train_domain_globs,
            resources=[
                policy_service_pb2.Resource(url=res.url, size=res.size, type=res.type.value, timestamp=res.order)
                for res in resources
            ],
        )

        policy_res = self.stub.GetPolicy(page)
        return Policy.from_dict(json.loads(policy_res.policy))
