""" This module implements some preprocessing functions for HAR files """
from typing import Dict, List

from blaze.chrome.har import Har, Timing
from blaze.config.environment import Resource, ResourceType
from blaze.util.seq import ordered_uniq


def get_har_entry_type(entry) -> ResourceType:
    """ Returns the ResourceType for the given HAR Entry """
    mime_str = entry.response.mime_type
    mime_map = [
        (["css"], ResourceType.CSS),
        (["html"], ResourceType.HTML),
        (["javascript"], ResourceType.SCRIPT),
        (["image"], ResourceType.IMAGE),
        (["font"], ResourceType.FONT),
    ]

    for (mime_types, resource_type) in mime_map:
        if any(mime_type in mime_str for mime_type in mime_types):
            return resource_type
    return ResourceType.OTHER


def compute_parent_child_relationships(res_list: List[Resource], timings: Dict[str, Timing]) -> List[Resource]:
    """
    Returns a new, ordered list of resources with parent-child relationships given the passed-in
    timing information. The input list is assumed to be ordered
    """
    # pre-map entry URL to its order
    order_map = {res.url: res.order for res in res_list}
    new_res_list = []
    for res in res_list:
        timing = timings.get(res.url, None)
        parent = order_map.get(timing.initiator, 0) if timing else 0

        new_res_list.append(
            Resource(
                url=res.url,
                type=res.type,
                size=res.size,
                order=res.order,
                group_id=res.group_id,
                source_id=res.source_id,
                initiator=parent,
                execution_ms=timing.execution_ms if timing else 0,
                fetch_delay_ms=timing.fetch_delay_ms if timing else 0,
                time_to_first_byte_ms=timing.time_to_first_byte_ms if timing else 0,
            )
        )

    return new_res_list


def har_entries_to_resources(har: Har) -> List[Resource]:
    """ Converts a list of HAR entries to a list of Resources """
    har_entries = har.log.entries

    # filter only entries that are requests for http(s) resources
    har_entries = [entry for entry in har_entries if entry.request.url.startswith("http")]
    # filter only entries for requests that completed
    har_entries = [entry for entry in har_entries if entry.response.status != 0]
    # sort the requests by initiated time
    har_entries = sorted(har_entries, key=lambda e: e.started_date_time)
    # select unique entries in case the same URL shows up twice
    har_entries = ordered_uniq(har_entries, key=lambda e: e.request.url)

    resource_list = []
    for (order, entry) in enumerate(har_entries):
        resource_list.append(
            Resource(
                url=entry.request.url,
                size=max(entry.response.body_size, 0) + max(entry.response.headers_size, 0),
                type=get_har_entry_type(entry),
                order=order,
                source_id=order,
            )
        )

    return compute_parent_child_relationships(resource_list, har.timings)
