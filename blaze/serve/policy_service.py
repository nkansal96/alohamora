from typing import Dict

import grpc

from blaze.config import client
from blaze.config import environment
from blaze.model.model import ModelInstance, SavedModel
from blaze.preprocess.resource import convert_policy_resource_to_environment_resource, resource_list_to_push_groups
from blaze.proto import policy_service_pb2
from blaze.proto import policy_service_pb2_grpc

class PolicyService(policy_service_pb2_grpc.PolicyServiceServicer):
  def __init__(self, saved_model: SavedModel = None):
    self.saved_model = saved_model
    self.policies: Dict[str, policy_service_pb2.Policy] = {}

  def GetPolicy(self, request: policy_service_pb2.Page, context: grpc.ServicerContext):
    if request.url not in self.policies:
      self.policies[request.url] = self.create_push_policy(request)
    return self.policies[request.url]

  def create_push_policy(self, page: policy_service_pb2.Page):
    model = self.create_model_instance(page)
    response = policy_service_pb2.Policy()
    for (source, push_list) in model.push_policy:
      policy_entry = response.policy.add() # pylint: disable=no-member
      policy_entry.source_url = source.url
      policy_entry.push_urls.extend([push.url for push in push_list])
    return response

  def create_model_instance(self, page: policy_service_pb2.Page) -> ModelInstance:
    # convert page resources to ordered push groups
    page_resources = sorted(page.resources, key=lambda r: r.timestamp)
    page_resources = list(map(convert_policy_resource_to_environment_resource, page_resources))
    push_groups = resource_list_to_push_groups(page_resources)
    # convert page network_type and device_speed to client environment
    client_environment = client.ClientEnvironment(
      device_speed=client.DeviceSpeed(page.device_speed),
      network_type=client.NetworkType(page.network_type),
      network_speed=0, # this one doesn't matter
    )
    # create environment config
    env_config = environment.EnvironmentConfig(request_url=page.url, push_groups=push_groups, replay_dir="")
    # instantiate a model for this config
    return self.saved_model.instantiate(env_config, client_environment)
