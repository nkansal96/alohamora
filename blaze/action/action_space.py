"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""
from typing import Dict, List, Tuple

import gym
import numpy as np

from blaze.config.environment import PushGroup, Resource
from blaze.logger import logger
from .action import Action


class ActionSpace(gym.spaces.Discrete):
    """
    ActionSpace defines the valid set of possible actions and faciliates the
    selection and management of actions as the agent explores. As actions are
    used, ActionSpace should be notified so that subsequent action selections
    do not result in repeated or invalid actions.Action

    ActionSpace uses a conditional geometric probability distribution for selecting
    push and source resources (in that order) and biases selection towards earlier
    resources
    """

    def __init__(self, push_groups: List[PushGroup]):
        self.rand = np.random.RandomState()
        self.push_groups = push_groups
        self.push_resources: List[Resource] = []
        self.action_id_map: Dict[Tuple[int, int, int], int] = {}
        self.actions: List[Action] = [Action()]
        for group in push_groups:
            max_depth = 100  # max(20, len(group.resources) // 3)
            for source in group.resources:
                if source.source_id != 0:
                    self.push_resources.append(source)
                for push in group.resources[source.source_id + 1 : (source.source_id + 1 + max_depth)]:
                    self.action_id_map[(group.id, source.source_id, push.source_id)] = len(self.actions)
                    self.actions.append(Action(len(self.actions), is_push=True, source=source, push=push))
        self.push_resources.sort(key=lambda r: r.order)
        logger.with_namespace("action_space").debug("initialized push resources", total=len(self.push_resources))
        super(ActionSpace, self).__init__(len(self.actions))

    def seed(self, seed):
        self.rand.seed(seed)

    def sample(self):
        # xxTODO: LIMIT THIS TO THE ACTION SPACE DEPTH RATHER THAN ALL RESOURCES IN THE PUSH GROUP
        # First decide whether we will push anything at all
        if self.rand.rand() < 0.2:
            return 0

        # Otherwise choose a push URL
        i = (self.rand.geometric(0.1) - 1) % len(self.push_resources)
        push_res = self.push_resources[i]
        p = push_res.source_id
        g = push_res.group_id

        # Choose a source URL
        group = next(group for group in self.push_groups if group.id == g)
        source_resources = [res for res in group.resources if res.order < push_res.order]
        source_resources.sort(key=lambda r: r.order)
        j = len(source_resources) - 1 - (self.rand.geometric(0.01) - 1) % len(source_resources)
        s = source_resources[j].source_id

        return self.action_id_map[(g, s, p)]

    def contains(self, x):
        return 0 <= x < len(self.actions)

    def decode_action_id(self, action_id) -> Action:
        """ Returns the Action object corresponding to the encoded action ID """
        return self.actions[action_id]

    def use_action(self, action: Action):
        """
        Marks the given action as used. It removes the pushed resource from the list
        of pushable resources, effectively removing a subset of the actions to prevent
        pushing the same resource twice. If the action was a noop, it doesn't do anything
        """
        log = logger.with_namespace("action_space.use_action")
        if action.is_noop:
            log.debug("noop: doing nothing", action=action)
            return
        for i, res in enumerate(self.push_resources):
            if res.order == action.push.order:
                del self.push_resources[i]
                log.debug("removed push resource", push=action.push.url, remaining=len(self.push_resources))
                break

    def __len__(self):
        return len(self.push_resources)
