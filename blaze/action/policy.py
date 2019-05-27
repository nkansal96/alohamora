"""
This module defines classes and methods related to tracking push policies
throughout a training episode and converting between the action space
representation and the actual URL representation
"""

import collections
from typing import Optional

from blaze.config.environment import Resource
from .action_space import ActionSpace


class Policy:
    """
    Policy defines the current push policy, marks actions as used as they are used,
    and provides functions to help convert the policy to a URL-based format
    """

    def __init__(self, action_space: ActionSpace):
        self.action_space = action_space
        self.total_actions = len(action_space)
        self.actions_taken = 0
        self.push_to_source = {}
        self.source_to_push = collections.defaultdict(set)
        self.default_source_to_push = collections.defaultdict(set)

    def __iter__(self):
        # This function assumes that the keys in self.source_to_push and self.default_source_to_push
        # are disjoint sets
        source_to_push = {**dict(self.default_source_to_push), **dict(self.source_to_push)}
        return iter(source_to_push.items())

    def __len__(self):
        return self.actions_taken

    @property
    def completed(self):
        """ Returns true if all actions have been taken """
        return self.actions_taken >= self.total_actions

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
        self.actions_taken += 1
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
