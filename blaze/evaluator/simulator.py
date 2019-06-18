"""
This module defines the classes and methods to implement a way to simulate
loading a webpage and simulating its page load time from a dependency graph
"""

from queue import PriorityQueue
from typing import List, NamedTuple, Optional, Set, Tuple

from blaze.action.policy import Policy
from blaze.config.environment import EnvironmentConfig, Resource, ResourceType
from blaze.config.client import ClientEnvironment
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
        self.rtt_latency_ms = rtt_latency_ms

    def __contains__(self, node: Node):
        """
        :return: True if the given node is already scheduled for download
        """
        return any(qi.node == node for qi in self.queue) or any(qi.node == node for qi in self.delayed)

    def __len__(self):
        return len(self.queue) + len(self.delayed)

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

    def add_with_delay(self, node: Node, delay_ms: int):
        """
        Adds an item to the queue but does not start it until the delay has occurred. Additionally,
        this method checks to see if a connection has been opened for the resource's origin. If not,
        it adds 2-RTT delay for the resource.
        """
        domain = Url.parse(node.resource.url).domain
        if domain not in self.connected_origins:
            delay_ms += 2 * self.rtt_latency_ms
        self.delayed.append(QueueItem(node, node.resource.size, domain, delay_ms))

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
            bytes_to_download = min([qi.bytes_left for qi in self.queue])
            time_ms_to_download = 1000 * bytes_to_download / self.bandwidth

        # OR, if the queue is empty, find the next delayed item to enqueue
        else:
            time_ms_to_download = min([qi.delay_ms_left for qi in self.delayed])
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
        self.res_to_node_map = {}
        self.create_execution_graph(env_config)

    def simulate_load_time(self, client_env: ClientEnvironment, policy: Optional[Policy] = None) -> float:
        """
        Simulates the page load time of a webpage in the given client environment
        with an optional push policy to also simulate.

        :return: The predicted page load time in milliseconds
        """

        pq = PriorityQueue()
        request_queue = RequestQueue(client_env.bandwidth, client_env.latency)
        completed_nodes = {}
        total_time_ms = 0

        # start the initial item
        pq.put((self.root.priority, self.root))
        request_queue.add(self.root)

        while not pq.empty():
            _, curr_node = pq.get()

            while curr_node not in completed_nodes:
                completed_this_step, time_ms_this_step = request_queue.step()
                total_time_ms += time_ms_this_step
                for node in completed_this_step:
                    completed_nodes[node] = total_time_ms + node.resource.execution_ms

            execution_delay_so_far = 0
            for (i, next_node) in enumerate(curr_node.children):
                pq.put((next_node.priority, next_node))
                if next_node not in completed_nodes and next_node not in request_queue:
                    # Server processing delay
                    delay = next_node.resource.time_to_first_byte_ms
                    # CPU slowdown for script exection time
                    delay += execution_delay_so_far * client_env.cpu_slowdown
                    # Amount of time the fetch was delayed since the script started
                    delay += next_node.resource.fetch_delay_ms
                    # if some of the fetch_delay overlaps with the parent script execution, delay that part of the time
                    delay += min(curr_node.resource.execution_ms, next_node.resource.fetch_delay_ms) * (
                        client_env.cpu_slowdown - 1
                    )
                    # if the previous node was a script, then don't consider its execution delay (speculative fetching)
                    if i > 0 and curr_node.children[i - 1].resource.type == ResourceType.SCRIPT:
                        delay -= curr_node.children[i - 1].resource.execution_ms

                    request_queue.add_with_delay(next_node, delay)

                    push_resources = policy.push_set_for_resource(next_node.resource) if policy else []
                    for push_res in push_resources:
                        if push_res not in completed_nodes and push_res not in request_queue:
                            push_node = self.res_to_node_map[push_res]
                            request_queue.add_with_delay(push_node, delay)

                execution_delay_so_far += next_node.resource.execution_ms

        return max(completed_nodes.values())

    def create_execution_graph(self, env_config: EnvironmentConfig):
        """
        Creates the execution graph from the environment config

        :param env_config: The environment resources to consider
        :return: The root node of the execution graph
        """

        # create a map of Nodes, mapping their order (basically their ID) to a Node for that resource
        # res_list = [res for group in env_config.push_groups for res in group.resources]
        res_list = env_config.har_resources
        self.node_map = {res.order: Node(resource=res, priority=res.order, children=[]) for res in res_list}
        self.res_to_node_map = {node.resource: node for node in self.node_map.values()}

        # for each resource, unless it's the start URL, add it as a child of its initiator
        for res in res_list:
            if res.url != env_config.request_url:
                self.node_map[res.initiator].children.append(self.node_map[res.order])

        # sort each child list by its order
        for node in self.node_map.values():
            node.children.sort(key=lambda n: n.resource.order)

        # The root is the node corresponding to the 0th order
        self.root = self.node_map[0]

    def print_execution_map(self):
        """
        Prints the execution graph
        """

        def recursive_print(root, depth=0):
            """
            Recursive helper method for printing the execution map
            """
            print(
                ("  " * depth)
                + f"({root.resource.order}, {root.resource.execution_ms}, {root.resource.fetch_delay_ms}, "
                + f"{ResourceType(root.resource.type).name}, {root.resource.url})"
            )
            for next_node in root.children:
                recursive_print(next_node, depth + 1)

        recursive_print(self.root)
