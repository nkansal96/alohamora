""" This module implements preprocessing functions for resources """
import pathlib
from typing import List

from blaze.config.environment import PushGroup, Resource, ResourceType
from blaze.proto import policy_service_pb2
from .url import Url


def resource_list_to_push_groups(res_list: List[Resource], train_domain_globs=None) -> List[PushGroup]:
    """ Convert an ordered list of resources to a list of PushGroups """

    # extract the list of domains and sort
    domains = sorted(list(set(Url.parse(res.url).domain for res in res_list)))
    # map domain to push group
    domain_to_push_group = {domain: i for (i, domain) in enumerate(domains)}
    # create the push groups
    is_trainable = lambda d: not train_domain_globs or any(map(pathlib.PurePath(d).match, train_domain_globs))
    trainable_domains = set(domain for domain in domains if is_trainable(domain))
    push_groups = [
        PushGroup(id=i, name=domain, resources=[], trainable=(domain in trainable_domains))
        for (i, domain) in enumerate(domains)
    ]
    # map the old order to the new order so that the initiators can be translated in place
    old_to_new_order_map = {res.order: order for (order, res) in enumerate(res_list)}

    for (order, res) in enumerate(res_list):
        url = Url.parse(res.url)
        group_id = domain_to_push_group[url.domain]
        new_res = Resource(
            url=res.url,
            size=res.size,
            type=res.type,
            order=order,
            group_id=group_id,
            source_id=len(push_groups[group_id].resources),
            initiator=old_to_new_order_map[res.initiator],
            execution_ms=res.execution_ms,
            fetch_delay_ms=res.fetch_delay_ms,
            time_to_first_byte_ms=res.time_to_first_byte_ms,
        )
        push_groups[new_res.group_id].resources.append(new_res)

    return push_groups


def convert_policy_resource_to_environment_resource(res: policy_service_pb2.Resource) -> Resource:
    """ Converts a policy_service_pb2.Resource to an environment.Resource """
    return Resource(url=res.url, size=res.size, type=ResourceType(res.type))
