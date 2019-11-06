"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""
from typing import List

import gym
import numpy as np

from blaze.config.environment import PushGroup
from .action import (
    Action,
    ActionIDType,
    PreloadActionIDType,
    PushActionIDType,
    NOOP_ACTION_ID,
    NOOP_PRELOAD_ACTION_ID,
    NOOP_PUSH_ACTION_ID,
)


class PushActionSpace(gym.spaces.Tuple):
    """
    PushActionSpace defines the valid set of possible push actions and faciliates the
    selection and management of actions as the agent explores. As actions are
    used, PushActionSpace should be notified so that subsequent action selections
    do not result in repeated or invalid Actions
    """

    def __init__(self, push_groups: List[PushGroup]):
        self.max_group_id = max(group.id for group in push_groups)
        self.max_source_id = max(r.source_id for group in push_groups for r in group.resources)
        self.group_id_to_source_id = {group.id: [r.source_id for r in group.resources] for group in push_groups}
        self.group_id_to_resource_map = {group.id: {r.source_id: r for r in group.resources} for group in push_groups}

        super().__init__((
            gym.spaces.Discrete(self.max_group_id + 1),
            gym.spaces.Discrete(self.max_source_id + 1),
            gym.spaces.Discrete(self.max_source_id + 1),
        ))

    def sample(self) -> PushActionIDType:
        if self.empty():
            return NOOP_PUSH_ACTION_ID

        # Choose a push group
        g = -1
        while g not in self.group_id_to_source_id or len(self.group_id_to_source_id[g]) <= 1:
            g = self.np_random.choice(list(self.group_id_to_source_id.keys()))

        # Choose a push URL
        p = 0
        while p == 0:
            p = self.np_random.choice(self.group_id_to_source_id[g])

        # Choose a source URL
        valid_sources = [r for r in self.group_id_to_source_id[g] if r < p]
        s = self.np_random.choice(valid_sources)

        return g, s, p

    def contains(self, x: PushActionIDType):
        if x == NOOP_PUSH_ACTION_ID:
            return True

        g, s, p = x
        return (
            g in self.group_id_to_source_id
            and s in self.group_id_to_resource_map[g].keys()
            and p in self.group_id_to_resource_map[g].keys()
            and s < p
        )

    def decode_action_id(self, action_id: PushActionIDType) -> Action:
        """ Returns the Action object corresponding to the encoded action ID """
        if action_id == NOOP_PUSH_ACTION_ID or not self.contains(action_id):
            return Action()

        g, s, p = action_id
        return Action(
            action_id=action_id,
            is_push=True,
            source=self.group_id_to_resource_map[g][s],
            push=self.group_id_to_resource_map[g][p],
        )

    def empty(self):
        """ Returns True if there are no more valid actions in the action space """
        return all(len(v) <= 1 for v in self.group_id_to_source_id.values())

    def use_action(self, action: Action):
        """
        Marks the given action as used. It removes the pushed resource from the list
        of pushable resources, effectively removing a subset of the actions to prevent
        pushing the same resource twice. If the action was a noop, it doesn't do anything
        """
        if action.is_noop:
            return
        g = action.push.group_id
        p = action.push.source_id
        self.group_id_to_source_id[g] = [r for r in self.group_id_to_source_id[g] if r != p]


class PreloadActionSpace(gym.spaces.Tuple):
    """
    PreloadActionSpace defines the valid set of possible preload actions and faciliates the
    selection and management of actions as the agent explores. As actions are
    used, PreloadctionSpace should be notified so that subsequent action selections
    do not result in repeated or invalid Actions
    """

    def __init__(self, push_groups: List[PushGroup]):
        self.order_to_resource_map = {r.order: r for group in push_groups for r in group.resources}
        self.preload_list = sorted([r.order for group in push_groups for r in group.resources if r.order != 0])
        self.source_list = sorted([r.order for group in push_groups for r in group.resources])
        self.max_order = self.source_list[-1]

        super().__init__((
            gym.spaces.Discrete(self.max_order + 1),
            gym.spaces.Discrete(self.max_order + 1),
        ))

    def sample(self) -> PreloadActionIDType:
        if self.empty():
            return NOOP_PRELOAD_ACTION_ID

        # choose a preload URL
        preload = self.np_random.choice(self.preload_list)

        # choose a source URL
        valid_sources = [r for r in self.source_list if r < preload]
        source = self.np_random.choice(valid_sources)
        return source, preload

    def contains(self, x: PreloadActionIDType):
        if x == NOOP_PRELOAD_ACTION_ID:
            return True

        source, preload = x
        return 0 <= source < preload <= self.max_order

    def decode_action_id(self, action_id: PreloadActionIDType) -> Action:
        """ Returns the Action object corresponding to the encoded action ID """
        if action_id == NOOP_PRELOAD_ACTION_ID or not self.contains(action_id):
            return Action()
        source, preload = action_id
        return Action(
            action_id=action_id,
            is_push=False,
            source=self.order_to_resource_map[source],
            push=self.order_to_resource_map[preload],
        )

    def use_action(self, action: Action):
        """
        Marks the given action as used. It removes the pushed resource from the list
        of pushable resources, effectively removing a subset of the actions to prevent
        pushing the same resource twice. If the action was a noop, it doesn't do anything
        """
        if not action.is_noop:
            self.preload_list = [r for r in self.preload_list if r != action.push.order]

    def empty(self):
        """ Returns true if there are no more valid actions in the action space """
        return not self.preload_list


class ActionSpace(gym.spaces.Tuple):
    """
    ActionSpace is a combination of a PushActionSpace and PreloadActionSpace and returns random
    actions from either one randomly, or chooses a no-op. It keeps track of which resources have been
    pushed/preloaded and notifies the underlying PushActionSpace and PreloadActionSpace respectively so that
    resources that were pushed are not preloaded, and vice-versa.
    """

    def __init__(self, push_groups: List[PushGroup], *, disable_push: bool = False, disable_preload: bool = False):
        assert not (disable_preload and disable_push), "Both push and preload cannot be disabled"

        self.push_groups = push_groups
        self.disable_push = disable_push
        self.disable_preload = disable_preload

        self.num_action_types = 2 if disable_push or disable_preload else 3
        self.action_types = list(range(self.num_action_types))
        self.action_type_space = gym.spaces.Discrete(self.num_action_types)
        self.push_space = PushActionSpace(push_groups)
        self.preload_space = PreloadActionSpace(push_groups)
        super().__init__((self.action_type_space, self.push_space, self.preload_space))

    def seed(self, seed):
        self.np_random.seed(seed)
        super().seed(seed)

    def sample(self):
        action_weights = [0.04] + ([(0.96 / (self.num_action_types - 1))] * (self.num_action_types - 1))
        action_type = self.np_random.choice(self.num_action_types, size=1, p=action_weights)[0]

        # Case: do nothing
        if action_type == 0:
            return NOOP_ACTION_ID

        # Push if action_type is 1 and push is not disabled
        if action_type == 1 and not self.disable_push:
            push_action = self.push_space.sample()
            if push_action == NOOP_PUSH_ACTION_ID:
                return NOOP_ACTION_ID
            return action_type, push_action, NOOP_PRELOAD_ACTION_ID

        # Preload if action type is 2 or action_type is 1 and push is disabled
        if action_type == 2 or self.disable_push:
            preload_action = self.preload_space.sample()
            if preload_action == NOOP_PRELOAD_ACTION_ID:
                return NOOP_ACTION_ID
            return action_type, NOOP_PUSH_ACTION_ID, preload_action

        # The case where preload is disabled and action_type is 2 will never happen
        return NOOP_ACTION_ID

    def decode_action(self, action: ActionIDType) -> Action:
        """ Decodes the given action ID into an Action object """
        (action_type, push_id, preload_id) = action
        if action_type == 0:
            return Action()

        is_push = action_type == 1 and not self.disable_push
        if is_push:
            return self.push_space.decode_action_id(push_id)
        return self.preload_space.decode_action_id(preload_id)

    def use_action(self, action: Action):
        """ Marks the action as used in both the push and preload spaces """
        self.push_space.use_action(action)
        self.preload_space.use_action(action)

    def empty(self):
        """ Returns true if there are no more valid actions in the action space """
        return self.push_space.empty() and self.preload_space.empty()
