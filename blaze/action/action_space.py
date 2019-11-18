"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""
from typing import Dict, List

import gym

from blaze.config.environment import PushGroup
from blaze.logger import logger
from .action import (
    Action,
    ActionIDType,
    PreloadActionIDType,
    PushActionIDType,
    NOOP_ACTION_ID,
    NOOP_PRELOAD_ACTION_ID,
    NOOP_PUSH_ACTION_ID,
)


def get_pushable_groups(push_groups: List[PushGroup]) -> Dict[int, PushGroup]:
    """ Returns a sublist of push_groups that only has groups that are pushable """
    return {
        i: g
        for (i, g) in enumerate(
            sorted([group for group in push_groups if len(group.resources) > 1], key=lambda g: g.id)
        )
    }


class PushActionSpace(gym.spaces.Tuple):
    """
    PushActionSpace defines the valid set of possible push actions and faciliates the
    selection and management of actions as the agent explores. As actions are
    used, PushActionSpace should be notified so that subsequent action selections
    do not result in repeated or invalid Actions
    """

    def __init__(self, push_groups: List[PushGroup]):
        push_groups = get_pushable_groups(push_groups)
        self.max_group_id = max(push_groups.keys())
        self.max_source_id = max(r.source_id for group in push_groups.values() for r in group.resources)
        self.group_id_to_source_id = {i: set(r.source_id for r in g.resources) for (i, g) in push_groups.items()}
        self.group_id_to_resource_map = {i: {r.source_id: r for r in g.resources} for (i, g) in push_groups.items()}

        super().__init__(
            (
                gym.spaces.Discrete(self.max_group_id + 1),
                gym.spaces.Discrete(self.max_source_id + 1),
                gym.spaces.Discrete(self.max_source_id + 1),
            )
        )

    def seed(self, seed):
        self.np_random.seed(seed)
        super().seed(seed)

    def sample(self) -> PushActionIDType:
        if self.empty():
            return NOOP_PUSH_ACTION_ID

        # Choose a push group
        g = self.np_random.choice(list(self.group_id_to_source_id.keys()))

        # Choose a push URL
        p = 0
        valid_push = list(self.group_id_to_source_id[g])
        while p == 0:
            p = self.np_random.choice(valid_push)

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
        if action_id == NOOP_PUSH_ACTION_ID:
            return Action()

        g, s, p = action_id
        while g not in self.group_id_to_source_id and g >= 0:
            g -= 1

        if g < 0:
            return Action()

        p = p % (max(self.group_id_to_resource_map[g].keys()) + 1)
        if p == 0:
            return Action()
        s = s % p

        return Action(
            action_id=(g, s, p),
            is_push=True,
            source=self.group_id_to_resource_map[g][s],
            push=self.group_id_to_resource_map[g][p],
        )

    def empty(self):
        """ Returns True if there are no more valid actions in the action space """
        return len(self) == 0

    def __len__(self):
        return sum(map(len, self.group_id_to_source_id.values()))

    def use_action(self, action: Action):
        """
        Marks the given action as used. It removes the pushed resource from the list
        of pushable resources, effectively removing a subset of the actions to prevent
        pushing the same resource twice. If the action was a noop, it doesn't do anything
        """
        if action.is_noop:
            return
        if action.is_push:
            g, _, p = action.action_id
        else:
            g = 0
            _, p = action.action_id
            for group_id, resources in self.group_id_to_resource_map.items():
                for res in resources.values():
                    if res.order == p:
                        g = group_id
                        break

        if g in self.group_id_to_source_id:
            self.group_id_to_source_id[g] -= {p}
            if len(self.group_id_to_source_id[g]) == 1:
                del self.group_id_to_source_id[g]


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

        super().__init__((gym.spaces.Discrete(self.max_order + 1), gym.spaces.Discrete(self.max_order + 1)))

    def seed(self, seed):
        self.np_random.seed(seed)
        super().seed(seed)

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
        source, preload = action_id
        if preload == 0 or action_id == NOOP_PRELOAD_ACTION_ID:
            return Action()

        source = source % preload
        if not self.contains((source, preload)):
            return Action()

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

    def __len__(self):
        return len(self.preload_list)


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

        self.num_action_types = 5 if disable_push or disable_preload else 6
        self.action_type_space = gym.spaces.Discrete(self.num_action_types)

        self.push_space = PushActionSpace(push_groups)
        self.preload_space = PreloadActionSpace(push_groups)

        super().__init__((self.action_type_space, *self.push_space.spaces, *self.preload_space.spaces))

    def seed(self, seed):
        self.np_random.seed(seed)
        self.push_space.seed(seed)
        self.preload_space.seed(seed)
        super().seed(seed)

    def sample(self):
        action_type = self.np_random.randint(0, self.action_type_space.n)
        action_type_id = 0 if action_type == 0 else ((action_type // 5) + 1)

        # Case: do nothing
        if action_type_id == 0:
            return NOOP_ACTION_ID

        # Push if action_type is 1 and push is not disabled
        if action_type_id == 1 and not self.disable_push:
            push_action = self.push_space.sample()
            if push_action == NOOP_PUSH_ACTION_ID:
                return NOOP_ACTION_ID
            return (action_type, *push_action, *NOOP_PRELOAD_ACTION_ID)

        # Preload if action type is 2 or action_type is 1 and push is disabled
        if action_type_id == 2 or self.disable_push:
            preload_action = self.preload_space.sample()
            if preload_action == NOOP_PRELOAD_ACTION_ID:
                return NOOP_ACTION_ID
            return (action_type, *NOOP_PUSH_ACTION_ID, *preload_action)

        # The case where preload is disabled and action_type is 2 will never happen
        return NOOP_ACTION_ID

    def decode_action(self, action: ActionIDType) -> Action:
        """ Decodes the given action ID into an Action object """
        # Temporary for compatibility:
        if len(action) == 6:
            action = (action[0], tuple(action[1:4]), tuple(action[4:]))

        (action_type, push_id, preload_id) = action
        action_type_id = 0 if action_type == 0 else ((action_type // 5) + 1)
        if action_type_id == 0:
            return Action()

        is_push = action_type_id == 1 and not self.disable_push
        if is_push:
            return self.push_space.decode_action_id(push_id)
        return self.preload_space.decode_action_id(preload_id)

    def use_action(self, action: Action):
        """ Marks the action as used in both the push and preload spaces """
        self.push_space.use_action(action)
        self.preload_space.use_action(action)
        logger.with_namespace("action_space").info(
            "used_action",
            action=repr(action),
            new_push_size=len(self.push_space),
            new_preload_size=len(self.preload_space),
        )

    def empty(self):
        """ Returns true if there are no more valid actions in the action space """
        return (self.disable_push or self.push_space.empty()) and (self.disable_preload or self.preload_space.empty())
