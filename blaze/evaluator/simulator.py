"""
This module defines the classes and methods to implement a way to simulate
loading a webpage and simulating its page load time from a dependency graph
"""

import copy
import json
from queue import PriorityQueue
from typing import List, NamedTuple, Optional, Set, Tuple

from blaze.action.policy import Policy
from blaze.config.environment import EnvironmentConfig, Resource, ResourceType
from blaze.config.client import ClientEnvironment
from blaze.logger import logger
from blaze.preprocess.url import Url


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
        multiplier = 2 if domain not in self.connected_origins else 1
        delay_ms += multiplier * self.rtt_latency_ms
        self.delayed.append(QueueItem(node, node.resource.size, domain, delay_ms))

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


class Simulator:
    """
    The main class that simulates a web page load. It is initialized using an EnvironmentConfig,
    which specifies the har_resources (a flat, ordered list of resources recorded from
    blaze.chrome.devtools.capture_har or blaze.chrome.devtools.capture_har_in_mahimahi that
    includes timing information about each request).
    """

    def __init__(self, env_config: EnvironmentConfig):
        self.root = None
        self.node_map = {}
        self.url_to_node_map = {}
        self.log = logger.with_namespace("simulator")
        self.create_execution_graph(env_config)

        self.pq = None
        self.request_queue = None
        self.completed_nodes = {}
        self.pushed_nodes = set()
        self.total_time_ms = 0

    def reset_simulation(self, client_env: ClientEnvironment):
        """
        Resets the state of the simulator with the given client environment

        :param client_env: the client environment to reset with
        """

        self.pq = PriorityQueue()
        self.request_queue = RequestQueue(client_env.bandwidth, client_env.latency)
        self.completed_nodes = {}
        self.pushed_nodes = set()
        self.total_time_ms = 0

    def schedule_push_resources(self, node: Node, delay: float, policy: Optional[Policy] = None):
        """
        Schedule all push resources for a given node with the given delay.

        :param node: The node to push resources for
        :param delay: The delay to schedule each pushed resource with
        :param policy: The push policy to use to look up which resources to push
        """

        push_resources = policy.push_set_for_resource(node.resource) if policy else []
        if push_resources:
            self.log.debug(
                "push resources for resource",
                resource=node.resource.url,
                push_results=[res.url for res in push_resources]
            )
        for push_res in push_resources:
            push_node = self.url_to_node_map.get(push_res.url)
            if push_node and push_node not in self.completed_nodes and push_node not in self.request_queue:
                self.pq.put((push_node.priority, push_node))
                self.request_queue.add_with_delay(push_node, delay + push_node.resource.time_to_first_byte_ms)
                self.pushed_nodes.add(push_node)
                self.log.debug(
                    "push resource",
                    time=self.total_time_ms,
                    delay=delay + push_node.resource.time_to_first_byte_ms,
                    source=node.resource.url,
                    push=push_res.url,
                )

    def step_request_queue(self, client_env: ClientEnvironment, policy: Optional[Policy] = None):
        """
        Steps through the request queue once and updates the simulator state based on the results

        :param client_env: the client environment to simulate
        :param policy: the push policy to simulate
        """

        completed_this_step, time_ms_this_step = self.request_queue.step()
        self.total_time_ms += time_ms_this_step
        for node in completed_this_step:
            self.completed_nodes[node] = self.total_time_ms + node.resource.execution_ms
            self.log.debug("resource completed", resource=node.resource.url, time=self.completed_nodes[node])
            self.schedule_child_requests(node, client_env, policy)

    def schedule_child_requests(self, parent: Node, client_env: ClientEnvironment, policy: Optional[Policy] = None):
        """
        Schedules all children for the given node

        :param parent: The node to schedule children for
        :param client_env: The client environment to simulate
        :param policy: The push policy to simulate
        """

        fetch_delay_correction = 0
        execution_delay = 0
        last_execution_delay = 0

        for child in parent.children:
            # Server processing delay
            child_delay = child.resource.time_to_first_byte_ms
            # Amount of time the fetch was delayed since the parent finished, minus the amount of time saved
            # from pushing
            child_delay += child.resource.fetch_delay_ms - fetch_delay_correction
            # Adjust the delay to account for slowed-down execution delay (and speculative fetching)
            child_delay += (execution_delay - last_execution_delay) * (client_env.cpu_slowdown - 1)
            # if some of the fetch_delay overlaps with the parent script execution, delay that part of the time
            child_delay += min(parent.resource.execution_ms, child.resource.fetch_delay_ms) * (
                client_env.cpu_slowdown - 1
            )

            # If it was pushed, calculate its delay as the difference between
            # when it was scheduled and how much time has passed since then
            if child in self.pushed_nodes:
                # get the time that the pushed resource would be complete
                push_completion_time = self.request_queue.estimated_completion_time(child)
                # get the time that this resource would have completed if it wasn't pushed
                rq = self.request_queue.copy()
                rq.remove(child)
                rq.add_with_delay(child, child_delay)
                completion_time = rq.estimated_completion_time(child)

                child_fetch_delay_correction = 0
                # case 1: pushed resource was partially downloaded at the point when this resource would have downloaded
                #         --> subtract the time already spent downloading
                if child_delay < push_completion_time < completion_time:
                    child_fetch_delay_correction = push_completion_time - child_delay
                # case 2: pushed resource completed downloading before this resource would have started downloading
                #         --> subtract the entire download time
                if push_completion_time < child_delay:
                    child_fetch_delay_correction = completion_time - child_delay
                # case 3: pushed resource will finish after this resource would have finished
                #         --> add the extra time spent downloading
                if push_completion_time > completion_time:
                    child_fetch_delay_correction = -(push_completion_time - completion_time)

                fetch_delay_correction += child_fetch_delay_correction
                self.pushed_nodes.remove(child)
                self.log.debug(
                    "correcting fetch delay",
                    parent=parent.resource.url,
                    resource=child.resource.url,
                    push_completion_time=push_completion_time,
                    orig_completion_time=completion_time,
                    download_time=completion_time - child_delay,
                    child_fetch_delay_correction=child_fetch_delay_correction,
                    total_fetch_delay_correction=fetch_delay_correction,
                )

            if child.resource.type == ResourceType.SCRIPT:
                execution_delay += child.resource.execution_ms
                last_execution_delay = child.resource.execution_ms

            if child not in self.completed_nodes and child not in self.request_queue:
                self.log.debug(
                    "scheduled resource",
                    resource=child.resource.url,
                    delay=child_delay,
                    ttfb=child.resource.time_to_first_byte_ms,
                    fetch_delay=child.resource.fetch_delay_ms,
                    execution=child.resource.execution_ms,
                    total_time=self.total_time_ms,
                )
                self.pq.put((child.priority, child))
                self.request_queue.add_with_delay(child, child_delay)
                self.schedule_push_resources(child, child_delay - child.resource.time_to_first_byte_ms, policy)

    def simulate_load_time(self, client_env: ClientEnvironment, policy: Optional[Policy] = None) -> float:
        """
        Simulates the page load time of a webpage in the given client environment
        with an optional push policy to also simulate.

        :return: The predicted page load time in milliseconds
        """
        self.log.debug("simulating page load with client environment", **client_env._asdict())
        if policy:
            self.log.debug("simulating page load with push policy:")
            self.log.debug(json.dumps(policy.as_dict, indent=4))
        self.reset_simulation(client_env)

        # start the initial item
        self.pq.put((self.root.priority, self.root))
        self.request_queue.add_with_delay(self.root, self.root.resource.time_to_first_byte_ms)

        # schedule push resources for the root
        self.schedule_push_resources(self.root, self.root.resource.time_to_first_byte_ms, policy)

        # process all subsequent requests
        while not self.pq.empty():
            _, curr_node = self.pq.get()
            while curr_node not in self.completed_nodes:
                self.step_request_queue(client_env, policy)
            self.schedule_child_requests(curr_node, client_env, policy)

        return max(self.completed_nodes.values())

    def create_execution_graph(self, env_config: EnvironmentConfig):
        """
        Creates the execution graph from the environment config

        :param env_config: The environment resources to consider
        :return: The root node of the execution graph
        """

        # create a map of Nodes, mapping their order (basically their ID) to a Node for that resource
        res_list = env_config.har_resources
        self.node_map = {res.order: Node(resource=res, priority=res.order, children=[]) for res in res_list}
        self.url_to_node_map = {node.resource.url: node for node in self.node_map.values()}

        # The root is the node corresponding to the 0th order
        self.root = self.node_map.get(0)

        # for each resource, unless it's the start resource, add it as a child of its initiator
        for res in res_list:
            if res != self.root.resource:
                self.node_map[res.initiator].children.append(self.node_map[res.order])

        # sort each child list by its order
        for node in self.node_map.values():
            node.children.sort(key=lambda n: n.resource.order)

    def print_execution_map(self):
        """
        Prints the execution graph
        """

        def recursive_print(root, depth=0):
            """
            Recursive helper method for printing the execution map
            """
            if not root:
                return
            print(
                ("  " * depth)
                + f"({root.resource.order}, {root.resource.execution_ms:.3f}, "
                + f"{root.resource.fetch_delay_ms:.3f}, {root.resource.size} B, "
                + f"{ResourceType(root.resource.type).name}, {root.resource.url})"
            )
            for next_node in root.children:
                recursive_print(next_node, depth + 1)

        recursive_print(self.root)
