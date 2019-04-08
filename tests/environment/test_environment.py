import pytest
from unittest import mock

from blaze.action import Action, ActionSpace, Policy
from blaze.config.client import ClientEnvironment
from blaze.environment import Environment
from blaze.environment.environment import NOOP_ACTION_REWARD
from blaze.evaluator import Analyzer

from tests.mocks.config import get_config

def get_action(action_space):
  # pick a non-noop action
  action_id = 0
  while action_id == 0:
    action_id = action_space.sample()
  return action_id

class TestEnvironment():
  def setup(self):
    self.environment = Environment(get_config())

  def test_init(self):
    env = self.environment
    assert isinstance(env, Environment)
    assert isinstance(env.client_environment, ClientEnvironment)
    assert isinstance(env.action_space, ActionSpace)
    assert isinstance(env.analyzer, Analyzer)
    assert isinstance(env.policy, Policy)
    assert env.config.train_config.push_groups == env.action_space.push_groups
    assert env.policy.action_space == env.action_space

  @mock.patch('blaze.evaluator.Analyzer.get_reward')
  def test_reset(self, mock_get_reward):
    mock_get_reward.return_value = 10

    # keep track of original number of resources
    num_push_resources = len(self.environment.action_space)
    action_id = get_action(self.environment.action_space)

    # step the environment and check that an action was successfully taken
    self.environment.step(action_id)
    assert len(self.environment.action_space) < num_push_resources
    assert self.environment.policy.actions_taken == 1

    # check that resetting the environment works
    self.environment.reset()
    assert len(self.environment.action_space) == num_push_resources
    assert self.environment.policy.actions_taken == 0

  def test_step_noop_action(self):
    try:
      noop_action = Action()
      obs, reward, _, info = self.environment.step(noop_action.action_id)
      assert reward == NOOP_ACTION_REWARD
      assert info['action'] == noop_action
      assert self.environment.policy.actions_taken == 1
      assert all(res['push_from'] == 0 for group in obs['push_groups'].values() for res in group.values())
    finally:
      self.environment.reset()

  @mock.patch('blaze.evaluator.Analyzer.get_reward')
  def test_step_action(self, mock_get_reward):
    try:
      action_rew = 1000
      mock_get_reward.return_value = action_rew

      action_id = get_action(self.environment.action_space)
      action = self.environment.action_space.decode_action_id(action_id)

      obs, reward, complete, info = self.environment.step(action_id)
      assert reward == action_rew
      assert not complete
      assert info['action'] == action
      assert self.environment.policy.actions_taken == 1
      assert self.environment.policy.resource_pushed_from(action.push) == action.source
      assert obs['push_groups'][str(action.g)][str(action.p)]['push_from'] == action.s
    finally:
      self.environment.reset()

  def test_render(self):
    with pytest.raises(NotImplementedError):
      self.environment.render()
