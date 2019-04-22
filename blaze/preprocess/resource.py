""" This module implements preprocessing functions for resources """
from typing import List

from blaze.config.environment import PushGroup, Resource, ResourceType
from blaze.proto import policy_service_pb2
from .url import Url

def resource_list_to_push_groups(res_list: List[Resource], train_domain_suffix="") -> List[PushGroup]:
  """ Convert an ordered list of resources to a list of PushGroups """
  # extract the list of domains and sort
  domains = sorted(list(set(Url.parse(res.url).domain for res in res_list)))
  # map domain to push group
  domain_to_push_group = {domain: i for (i, domain) in enumerate(domains)}
  # create the push groups
  push_groups = [PushGroup(id=i, name=domain, resources=[], trainable=domain.endswith(train_domain_suffix))
                 for (i, domain) in enumerate(domains)]

  for (order, res) in enumerate(res_list):
    url = Url.parse(res.url)
    group_id = domain_to_push_group[url.domain]
    new_res = Resource(
      url=res.url,
      size=res.size,
      order=order,
      group_id=group_id,
      source_id=len(push_groups[group_id].resources),
      type=res.type,
    )
    push_groups[new_res.group_id].resources.append(new_res)

  return push_groups

def convert_policy_resource_to_environment_resource(res: policy_service_pb2.Resource) -> Resource:
  """ Converts a policy_service_pb2.Resource to an environment.Resource """
  return Resource(url=res.url, size=res.size, type=ResourceType(res.type))
