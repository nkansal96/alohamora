"""
This module defines classes and methods related to tracking push policies
throughout a training episode and converting between the action space
representation and the actual URL representation
"""

import collections
from typing import Optional, Set

from blaze.config.environment import Resource, ResourceType
from .action_space import ActionSpace


class Policy:
    """
    Policy defines the current push policy, marks actions as used as they are used,
    and provides functions to help convert the policy to a URL-based format
    """

    def __init__(self, action_space: ActionSpace):
        self.action_space = action_space
        self.total_actions = len(action_space)
        self.steps_taken = 0
        self.push_to_source = {}
        self.source_to_push = collections.defaultdict(set)
        self.default_source_to_push = collections.defaultdict(set)

    def __iter__(self):
        # This function assumes that the keys in self.source_to_push and self.default_source_to_push
        # are disjoint sets
        source_to_push = {**dict(self.default_source_to_push), **dict(self.source_to_push)}
        return iter(source_to_push.items())

    def __len__(self):
        return self.steps_taken

    @property
    def total_steps(self):
        """ Returns the maximum number of steps to take before completing the policy """
        return min(self.total_actions, max(10, self.total_actions // 2))

    @property
    def steps_remaining(self):
        """ Returns the number of steps remaining before the policy is complete """
        return self.total_steps - self.steps_taken

    @property
    def completed(self):
        """ Returns true if all steps have been taken """
        return self.steps_remaining <= 0

    @property
    def observable(self):
        """
        Returns the observable push policy, which is only the set of items that are a subset
        of the trainable push groups
        """
        return iter(self.source_to_push.items())

    @property
    def as_dict(self):
        """
        Constructs a dictionary representation of the push policy for JSON seralization
        """
        policy = {}
        for source, push_list in self:
            policy[source.url] = [p.url for p in push_list]
        return policy

    def apply_action(self, action_id: int):
        """ Given an encoded action, applies the action towards the push policy """
        action = self.action_space.decode_action_id(action_id)
        if not action.is_noop and action.push not in self.push_to_source:
            self.push_to_source[action.push] = action.source
            self.source_to_push[action.source].add(action.push)
            self.action_space.use_action(action)
        self.steps_taken += 1
        return not action.is_noop

    def add_default_action(self, source: Resource, push: Resource):
        """
        Adds a default entry to the push policy, which is always pushed but not
        observable to the environment
        """
        self.default_source_to_push[source].add(push)

    def resource_pushed_from(self, push: Resource) -> Optional[Resource]:
        """
        Returns the resource that the given resource is pushed from, or None if none
        """
        if push not in self.push_to_source:
            return None
        return self.push_to_source[push]

    def push_set_for_resource(self, source: Resource) -> Set[Resource]:
        """
        Returns the set of resources pushed for the given source resource
        """
        return self.source_to_push[source]

    @staticmethod
    def from_dict(policy_dict: dict):
        """
        Returns a Policy instantiated from a simple dictionary of source URLs to lists of push URLs. The returned
        Policy will only be useful for display purposes, as the action space will be instantiated with an empty
        list of push groups.
        """
        policy = Policy(ActionSpace([]))
        for (source, deps) in policy_dict.items():
            policy.source_to_push[Resource(url=source, size=0, type=ResourceType.NONE)] = set(
                Resource(url=push, size=0, type=ResourceType.NONE) for push in deps
            )
            for push in deps:
                policy.push_to_source[Resource(url=push, size=0, type=ResourceType.NONE)] = Resource(
                    url=source, size=0, type=ResourceType.NONE
                )
        return policy
