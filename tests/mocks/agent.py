from typing import Optional
from blaze.action import ActionSpace
from blaze.action.action import NOOP_ACTION_ID

import numpy as np


def mock_agent_with_action_space(action_space: ActionSpace):
    return lambda **kwargs: MockAgent(action_space, **kwargs)


class MockAgent:
    def __init__(self, action_space: Optional[ActionSpace] = None, **kwargs):
        self.action_space = action_space
        self.sampled_actions = []
        self.kwargs = kwargs
        self.file_path = None
        self.observations = []

    def compute_action(self, observation: dict, **kwargs):
        self.observations.append(observation)
        # Don't choose a no-op for the first one, else this doesn't really simulate anything
        action_id = NOOP_ACTION_ID
        while action_id == NOOP_ACTION_ID and not self.sampled_actions:
            action_id = self.action_space.sample()
        # The action agent converts the sampled value to an array of (1,) numpy arrays
        action = [np.array([x]) for x in action_id]
        self.sampled_actions.append(action)
        return [action]

    def restore(self, file_path):
        self.file_path = file_path
