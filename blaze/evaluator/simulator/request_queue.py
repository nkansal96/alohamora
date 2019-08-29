"""
This module defines the classes and methods to implement a way to simulate
loading a webpage and simulating its page load time from a dependency graph
"""

import copy
from collections import defaultdict
from typing import DefaultDict, List, NamedTuple, Set, Tuple

from blaze.config.environment import Resource
from blaze.preprocess.url import Url

from .tcp_state import TCPState


class Node(NamedTuple):
    """ A Node in the Simulator graph """

    resource: Resource
    priority: int
    children: List["Node"] = []

    def __hash__(self):
        return id(self)

    def __eq__(self, other: "Node"):
        return self.resource == other.resource


class QueueItem:
    """ An item in the RequestQueue """

    def __init__(self, node: Node, size: int, origin: str, delay_ms: int = 0):
        self.node = node
        self.bytes_left = size
        self.origin = origin
        self.delay_ms_left = delay_ms


class RequestQueue:
    """
    RequestQueue simulates ongoing network requests and the amount of time it would
    take to complete them.
    """

    def __init__(self, bandwidth_kbps: int, rtt_latency_ms: int):
        self.queue: List[QueueItem] = []
        self.delayed: List[QueueItem] = []
        self.connected_origins: Set[str] = set()
        # convert kilobits per second (kbps) to bytes per second (Bps)
        self.link_bandwidth_bps = bandwidth_kbps * (1000 / 8)
        self.bandwidth_kbps = bandwidth_kbps
        self.rtt_latency_ms = rtt_latency_ms
        # model TCP dynamics per domain
        self.tcp_state: DefaultDict[TCPState] = defaultdict(TCPState)

    def __contains__(self, node: Node):
        """
        :return: True if the given node is already scheduled for download
        """
        return any(qi.node == node for qi in self.queue) or any(qi.node == node for qi in self.delayed)

    def __len__(self):
        return len(self.queue) + len(self.delayed)

    def copy(self) -> "RequestQueue":
        """
        :return: a copy of the request queue
        """
        rq = RequestQueue(self.bandwidth_kbps, self.rtt_latency_ms)
        rq.queue = [copy.copy(qi) for qi in self.queue]
        rq.delayed = [copy.copy(qi) for qi in self.delayed]
        rq.connected_origins = set(self.connected_origins)
        rq.tcp_state = copy.deepcopy(self.tcp_state)
        return rq

    @property
    def bandwidth(self):
        """
        Calculates the bandwidth available to each currently-ongoing request. This is
        calculated as the total link bandwidth split evenly amongst all of the currently-
        downloading files, but could be made more sophisticated by taking into account
        per-domain bandwidth limits.
        """
        return self.link_bandwidth_bps / (len(self.queue) or 1)

    def add(self, node: Node):
        """ Adds an item to the queue for immediate download """
        self.add_with_delay(node, 0)

    def remove(self, node: Node):
        """
        Removes the given node from the request queue
        :param node: the node to remove
        """

        self.queue = [qi for qi in self.queue if qi.node != node]
        self.delayed = [qi for qi in self.delayed if qi.node != node]

    def add_with_delay(self, node: Node, delay_ms: int):
        """
        Adds an item to the queue but does not start it until the delay has occurred. Additionally,
        this method checks to see if a connection has been opened for the resource's origin. If not,
        it adds 2-RTT delay for the resource.
        """

        domain = Url.parse(node.resource.url).domain
        num_rtts = self.tcp_state[domain].round_trips_needed_for_bytes(node.resource.size)
        if domain not in self.connected_origins:
            num_rtts += 1

        delay_ms = max(0, delay_ms + (num_rtts * self.rtt_latency_ms))
        queue_item = QueueItem(node, node.resource.size, domain, delay_ms)
        if delay_ms <= 0:
            self.queue.append(queue_item)
        else:
            self.delayed.append(queue_item)

    def estimated_completion_time(self, node: Node) -> float:
        """
        Runs through a copy of the request queue and returns the relative time offset
        at which the given node would have completed.

        :param node: The node to estimate the completion time of
        :return: 0 if the node is not in the request queue; the relative time offset
                 of completion otherwise
        """

        if node not in self:
            return 0
        rq = self.copy()
        total_time = 0
        completed_nodes, step_ms = [], 0
        while rq and node not in completed_nodes:
            completed_nodes, step_ms = rq.step()
            total_time += step_ms
        return total_time

    def step(self) -> Tuple[List[Node], float]:
        """
        Performs one step through of the request queue, which simulates downloading until
        one item finishes downloading (or more, if they finish at the same time). The method
        then removes the finished downloads from the request queue and reduces the number
        of bytes left to download for the remaining items correspondingly

        :return: a tuple where the first value is a list of simulator Nodes that finished
        downloading in this step; the second value is the time in milliseconds it took to
        download those items in this step
        """

        # check if the queue is empty
        if not self.queue and not self.delayed:
            return [], 0.0

        # find the item with the least number of bytes left to download
        if self.queue:
            bytes_to_download = min(qi.bytes_left for qi in self.queue)
            time_ms_to_download = 1000 * bytes_to_download / self.bandwidth

        # OR, if the queue is empty, find the next delayed item to enqueue
        else:
            time_ms_to_download = min(qi.delay_ms_left for qi in self.delayed)
            bytes_to_download = (time_ms_to_download * self.bandwidth) / 1000

        # Reduce all delayed items by time_ms_to_download
        for item in self.delayed:
            item.delay_ms_left -= time_ms_to_download

        # Reduce all queue elements by bytes_to_download
        for item in self.queue:
            item.bytes_left -= bytes_to_download

        # Update the idle time for each TCP state
        domains_downloaded_from = set(Url.parse(item.node.resource.url).domain for item in self.queue)
        for domain, tcp_state in self.tcp_state.items():
            if domain in domains_downloaded_from:
                tcp_state.add_bytes_sent(bytes_to_download)
            else:
                tcp_state.add_time_since_last_byte(time_ms_to_download)

        # Find all delayed items that are ready to be queued
        delayed_items_to_queue = [qi for qi in self.delayed if qi.delay_ms_left < 0.01]
        # Find all queued items that have been completed and are ready for removal
        completed_nodes = [qi.node for qi in self.queue if qi.bytes_left == 0]

        # add origins for newly-queued items
        for item in delayed_items_to_queue:
            self.connected_origins.add(item.origin)

        # update the delayed queue, removing items ready to be queued
        self.delayed = [qi for qi in self.delayed if qi.delay_ms_left > 0.01]
        # update the queue, removing items that are done and adding delayed items ready to be queued
        self.queue = [qi for qi in self.queue if qi.bytes_left > 0] + delayed_items_to_queue

        # return nodes that finished downloading and the total time took in this step
        return completed_nodes, time_ms_to_download
