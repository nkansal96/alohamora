import gym

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.environment.observation import get_observation, get_observation_space

from tests.mocks.config import get_push_groups

class TestGetObservationSpace():
  def test_get_observation_space(self):
    space = get_observation_space()
    assert isinstance(space, gym.spaces.Dict)

class TestGetObservation():
  def setup(self):
    self.push_groups = get_push_groups()
    self.observation_space = get_observation_space()
    self.client_environment = get_random_client_environment()

  def test_get_default_observation(self):
    action_space = ActionSpace(self.push_groups)
    policy = Policy(action_space)

    obs = get_observation(self.client_environment, self.push_groups, policy)
    assert isinstance(obs, dict)
    assert self.observation_space.contains(obs)

    # assert that the client environment is correctly captured
    assert obs['client']['network_type'] == self.client_environment.network_type.value
    assert obs['client']['device_speed'] == self.client_environment.device_speed.value

    # assert that all resources are not pushed initially
    assert all(res['push_from'] == 0 for (g, group) in obs['push_groups'].items() for (r, res) in group.items())

    # assert that the push_groups are encoded correctly
    for g, group in enumerate(self.push_groups):
      for s, res in enumerate(group.resources):
        assert obs['push_groups'][str(g)][str(s)]['enabled'] == 1
        assert obs['push_groups'][str(g)][str(s)]['size'] == res.size
        assert obs['push_groups'][str(g)][str(s)]['type'] == res.type.value

  def test_observation_with_nonempty_policy(self):
    action_space = ActionSpace(self.push_groups)
    policy = Policy(action_space)

    # do some actions and check the observation space over time
    for _ in range(len(action_space) - 1):
      # get an action and apply it in the policy
      action_id = action_space.sample()
      policy.apply_action(action_id)

      # get the observation
      obs = get_observation(self.client_environment, self.push_groups, policy)
      assert self.observation_space.contains(obs)

      # make sure the push sources are recorded correctly
      for (source, push) in policy:
        for push_res in push:
          assert obs['push_groups'][str(source.group_id)][str(push_res.source_id)]["push_from"] == source.source_id

      # check that all other resources are not pushed
      pushed_res = set((source.group_id, push_res.source_id) for (source, push) in policy for push_res in push)
      assert all(res['push_from'] == 0
                 for (g, group) in obs['push_groups'].items()
                 for (r, res) in group.items()
                 if (int(g), int(r)) not in pushed_res)
