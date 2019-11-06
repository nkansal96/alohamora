"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""

from typing import Optional, Tuple, Union

import numpy as np

from blaze.config.environment import Resource


PushActionIDType = Tuple[int, int, int]
PreloadActionIDType = Tuple[int, int]
ActionIDType = Tuple[int, PushActionIDType, PreloadActionIDType]

NOOP_PUSH_ACTION_ID = np.array((0, 0, 0))
NOOP_PRELOAD_ACTION_ID = np.array((0, 0))
NOOP_ACTION_ID = np.array((0, NOOP_PUSH_ACTION_ID, NOOP_PRELOAD_ACTION_ID))


class Action:
    """
    Action describes a single, valid action that the agent can take. It consists of
    a pair of resources (source, push) which describe the resource that should be pushed
    upon a request for a given resource
    """

    def __init__(
        self,
        action_id: Optional[Union[PushActionIDType, PreloadActionIDType]] = None,
        *,
        is_push: Optional[bool] = None,
        source: Optional[Resource] = None,
        push: Optional[Resource] = None,
    ):
        self.action_id = action_id
        self.source = source
        self.push = push
        self.is_push = is_push or False

    @property
    def is_preload(self):
        """ Returns true if this action represents a preload """
        return not self.is_push

    @property
    def is_noop(self):
        """ Returns true if this action is a no-op """
        return self.action_id is None

    def __repr__(self):
        if self.is_noop:
            return "Action(noop)"
        return f"Action({'push' if self.is_push else 'preload'}, source={self.source.url}, push={self.push.url})"

    def __eq__(self, action):
        return self.action_id == action.action_id
