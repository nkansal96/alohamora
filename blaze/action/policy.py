"""
This module defines classes and methods related to tracking push policies
throughout a training episode and converting between the action space
representation and the actual URL representation
"""

import collections
from typing import Optional, Set, Tuple, Union

import numpy as np

from blaze.config.environment import Resource, ResourceType
from .action import Action
from .action_space import ActionSpace


class Policy:
    """
    Policy defines the current push/preload policy, marks actions as used as they are used,
    and provides functions to help convert the policy to a URL-based format
    """

    def __init__(self, action_space: Optional[ActionSpace] = None):
        self.action_space = action_space
        self.total_actions = len(action_space or [])
        self.steps_taken = 0
        # Maps the source object for each pushed/preloaded object
        self.push_to_source = {}
        self.preload_to_source = {}
        # Maps the push/preload objects for each source object
        self.source_to_push = collections.defaultdict(set)
        self.source_to_preload = collections.defaultdict(set)
        # Maps the default push/preload objects (not visible to RL agent) for each source object
        self.default_source_to_push = collections.defaultdict(set)
        self.default_source_to_preload = collections.defaultdict(set)

    @property
    def push(self):
        """
        This function assumes that the keys in self.source_to_push and self.default_source_to_push
        are disjoint sets

        :return: An iterator over all source resources and corresponding sets of resources pushed for that resource
        """
        source_to_push = {**dict(self.default_source_to_push), **dict(self.source_to_push)}
        return iter(source_to_push.items())

    @property
    def preload(self):
        """
        This function assumes that the keys in self.source_to_preload and self.default_source_to_preload
        are disjoint sets

        :return: An iterator over all source resources and corresponding sets of resources preloaded for that resource
        """
        source_to_preload = {**dict(self.default_source_to_preload), **dict(self.source_to_preload)}
        return iter(source_to_preload.items())

    def __len__(self):
        return self.steps_taken

    @property
    def observable_push(self):
        """
        Returns the observable push policy, which is only the set of items that are a subset
        of the trainable push groups
        """
        return iter(self.source_to_push.items())

    @property
    def observable_preload(self):
        """
        Returns the observable preload policy, which is only the set of items that are a subset
        of the trainable push groups
        """
        return iter(self.source_to_preload.items())

    @property
    def as_dict(self):
        """
        Constructs a dictionary representation of the push policy for JSON seralization
        """
        policy = {"push": {}, "preload": {}}
        for s, push_list in self.push:
            if push_list:
                policy["push"][s.url] = [{"url": p.url, "type": ResourceType(p.type).name} for p in push_list]
        for s, preload_list in self.preload:
            if preload_list:
                policy["preload"][s.url] = [{"url": p.url, "type": ResourceType(p.type).name} for p in preload_list]
        return policy

    def apply_action(self, action: Union[Action, Tuple[int, Tuple[int, int, int], Tuple[int, int]]]):
        """ Given an encoded action, applies the action towards the push policy """
        if isinstance(action, (tuple, np.ndarray)):
            action = self.action_space.decode_action(action)
        action_applied = False
        if not action.is_noop:
            if action.is_push and action.push not in self.push_to_source:
                self.push_to_source[action.push] = action.source
                self.source_to_push[action.source].add(action.push)
                action_applied = True
            elif action.is_preload and action.push not in self.preload_to_source:
                self.preload_to_source[action.push] = action.source
                self.source_to_preload[action.source].add(action.push)
                action_applied = True
        self.steps_taken += 1 if action_applied else 0
        return action_applied

    def add_default_push_action(self, source: Resource, push: Resource):
        """
        Adds a default entry to the push policy, which is always pushed but not
        observable to the environment
        """
        self.default_source_to_push[source].add(push)

    def add_default_preload_action(self, source: Resource, preload: Resource):
        """
        Adds a default entry to the preload policy, which is always preloaded but not
        observable to the environment
        """
        self.default_source_to_preload[source].add(preload)

    def resource_pushed_from(self, push: Resource) -> Optional[Resource]:
        """
        Returns the resource that the given resource is pushed from, or None if none
        """
        if push not in self.push_to_source:
            return None
        return self.push_to_source[push]

    def resource_preloaded_from(self, preload: Resource) -> Optional[Resource]:
        """
        Returns the resource that the given resource is preloaded from, or None if none
        """
        if preload not in self.preload_to_source:
            return None
        return self.preload_to_source[preload]

    def push_set_for_resource(self, source: Resource) -> Set[Resource]:
        """
        Returns the set of resources pushed for the given source resource
        """
        default_push_resources = self.default_source_to_push[source]
        push_resources = self.source_to_push[source]
        return push_resources | default_push_resources

    def preload_set_for_resource(self, source: Resource) -> Set[Resource]:
        """
        Returns the set of resources preloaded for the given source resource
        """
        default_preload_resources = self.default_source_to_preload[source]
        preload_resources = self.source_to_preload[source]
        return preload_resources | default_preload_resources

    @staticmethod
    def from_dict(policy_dict: dict) -> "Policy":
        """
        Returns a Policy instantiated from a simple dictionary of source URLs to lists of push URLs. The returned
        Policy will only be useful for display purposes, as the action space will be instantiated with an empty
        list of push groups.
        """
        policy = Policy()
        for ptype, policy_obj in policy_dict.items():
            if ptype not in {"push", "preload"}:
                continue

            action_set = policy.source_to_push if ptype == "push" else policy.source_to_preload
            reverse_map = policy.push_to_source if ptype == "push" else policy.preload_to_source

            for (source, deps) in policy_obj.items():
                action_set[Resource(url=source, size=0, type=ResourceType.NONE)] = set(
                    Resource(url=push["url"], size=0, type=ResourceType[push["type"]]) for push in deps
                )
                for obj in deps:
                    reverse_map[Resource(url=obj["url"], size=0, type=ResourceType[obj["type"]])] = Resource(
                        url=source, size=0, type=ResourceType.NONE
                    )
        policy.steps_taken += sum(map(len, policy.source_to_push.values()))
        policy.steps_taken += sum(map(len, policy.source_to_preload.values()))
        return policy
