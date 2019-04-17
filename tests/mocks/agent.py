from typing import Optional
from blaze.action import ActionSpace

def mock_agent_with_action_space(action_space: ActionSpace):
  return lambda *args, **kwargs: MockAgent(action_space, *args, **kwargs)

class MockAgent():
  def __init__(self, action_space: Optional[ActionSpace] = None, **kwargs):
    self.action_space = action_space
    self.sampled_actions = []
    self.kwargs = kwargs
    self.file_path = None
    self.observations = []

  def compute_action(self, observation: dict):
    self.observations.append(observation)
    action = self.action_space.sample()
    self.sampled_actions.append(action)
    return action

  def restore(self, file_path):
    self.file_path = file_path
