""" Defines classes and methods to instantiate, evaluate, and serve push policies """
import json
from typing import Dict

import grpc

from blaze.config import client
from blaze.config import environment
from blaze.config.config import get_config
from blaze.model.model import ModelInstance, SavedModel
from blaze.proto import policy_service_pb2
from blaze.proto import policy_service_pb2_grpc


class PolicyService(policy_service_pb2_grpc.PolicyServiceServicer):
    """
    Implements the PolicyServerServicer interface to satsify the proto-defined RPC interface for
    serving push policies
    """

    def __init__(self, saved_model: SavedModel, config=get_config()):
        self.config = config
        self.saved_model = saved_model
        self.policies: Dict[str, policy_service_pb2.Policy] = {}

    def GetPolicy(self, request: policy_service_pb2.Page, context: grpc.ServicerContext) -> policy_service_pb2.Policy:
        return self.create_policy(request)

    def create_policy(self, page: policy_service_pb2.Page) -> policy_service_pb2.Policy:
        """ Creates and formats a push policy for the given page """
        model = self.create_model_instance(page)
        response = policy_service_pb2.Policy()
        response.policy = json.dumps(model.policy.as_dict)
        return response

    def create_model_instance(self, page: policy_service_pb2.Page) -> ModelInstance:
        """ Instantiates a model for the given page """
        # convert page network_type and device_speed to client environment
        client_env = client.get_client_environment_from_parameters(
            page.bandwidth_kbps, page.latency_ms, page.cpu_slowdown
        )
        # create environment config
        env_config = environment.EnvironmentConfig.deserialize(page.manifest)
        # instantiate a model for this config - TODO is to populate cached_urls
        config = self.config.with_mutations(env_configs=[env_config], client_env=client_env, cached_urls=set())
        return self.saved_model.instantiate(config)
