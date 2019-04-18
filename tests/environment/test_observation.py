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
    assert all(res[3] == 0 for res in obs['resources'].values())

    # assert that the push_groups are encoded correctly
    for group in self.push_groups:
      for res in group.resources:
        assert obs['resources'][str(res.order)][0] == 1
        assert obs['resources'][str(res.order)][1] == res.type.value
        assert obs['resources'][str(res.order)][2] == res.size//1000 # encoded in KB

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
          assert obs['resources'][str(push_res.order)][3] == source.order

      # check that all other resources are not pushed
      pushed_res = set(push_res.order for (source, push) in policy for push_res in push)
      assert all(res[3] == 0
                 for order, res in obs['resources'].items()
                 if int(order) not in pushed_res)
