import random

import pytest
from unittest import mock

from blaze.action import Action, ActionIDType, ActionSpace, Policy
from blaze.action.action import NOOP_ACTION_ID
from blaze.config.client import ClientEnvironment
from blaze.config.config import get_config
from blaze.environment import Environment
from blaze.environment.environment import NOOP_ACTION_REWARD
from blaze.evaluator import Analyzer

from tests.mocks.config import get_config


def get_action(action_space: ActionSpace) -> ActionIDType:
    # pick a non-noop action
    action = NOOP_ACTION_ID
    while action_space.decode_action(action).is_noop:
        action = action_space.sample()
    return action


class TestEnvironment:
    def setup(self):
        self.environment = Environment(get_config())
        self.environment.action_space.seed(2048)
        self.push_groups = self.environment.env_config.push_groups
        self.trainable_push_groups = self.environment.env_config.trainable_push_groups

    def test_init(self):
        env = self.environment
        assert isinstance(env, Environment)
        assert isinstance(env.client_environment, ClientEnvironment)
        assert isinstance(env.action_space, ActionSpace)
        assert isinstance(env.analyzer, Analyzer)
        assert isinstance(env.policy, Policy)
        assert env.config.env_config.push_groups == get_config().env_config.push_groups
        assert env.action_space.push_groups == self.push_groups
        assert env.policy.action_space == env.action_space

    def test_init_with_dict_env(self):
        env = Environment(get_config()._asdict())
        assert isinstance(env, Environment)
        assert env.config == get_config()

    def test_init_with_invalid_config_type(self):
        with pytest.raises(AssertionError):
            Environment((1, 2, 3))

    @mock.patch("blaze.evaluator.Analyzer.get_reward")
    def test_reset(self, mock_get_reward):
        mock_get_reward.return_value = 10

        action_space = self.environment.action_space
        action_id = get_action(self.environment.action_space)

        # step the environment and check that an action was successfully taken
        self.environment.step(action_id)
        assert self.environment.policy.steps_taken == 1

        # check that resetting the environment works
        obs = self.environment.reset()
        assert self.environment.action_space is not action_space
        assert self.environment.policy.steps_taken == 0
        assert obs and isinstance(obs, dict)
        assert self.environment.observation_space.contains(obs)

    # def test_initialize_environment_chooses_random_default_push_group(self):
    #     assert not self.environment.policy.push_to_source
    #     # there is exactly one non-trainable group, so that would be the one that is
    #     # "randomly" selected
    #     non_trainable_group = next(group for group in self.environment.env_config.push_groups if not group.trainable)
    #     source = non_trainable_group.resources[0]
    #
    #     assert len(self.environment.policy.default_source_to_push) == 1
    #     assert source in self.environment.policy.default_source_to_push
    #     assert len(self.environment.policy.default_source_to_push[source]) == len(non_trainable_group.resources) - 1

    # def test_initialize_only_trains_on_trainable_push_groups(self):
    #     assert self.environment.action_space.push_groups == self.trainable_push_groups

    def test_step_noop_action(self):
        try:
            obs, reward, _, info = self.environment.step(NOOP_ACTION_ID)
            assert reward == NOOP_ACTION_REWARD
            assert info["action"].is_noop
            assert self.environment.policy.steps_taken == 0
            # res[-2] and res[-1] refer to the push/preload source respectively
            assert all(res[-2] == 0 for res in obs["resources"].values())
            assert all(res[-1] == 0 for res in obs["resources"].values())
        finally:
            self.environment.reset()

    @mock.patch("blaze.evaluator.Analyzer.get_reward")
    def test_step_action(self, mock_get_reward):
        try:
            action_rew = 1000
            mock_get_reward.return_value = action_rew

            action_id = get_action(self.environment.action_space)
            action = self.environment.action_space.decode_action(action_id)

            obs, reward, complete, info = self.environment.step(action_id)
            assert reward != NOOP_ACTION_REWARD
            assert not complete
            assert info["action"] == action
            assert self.environment.policy.steps_taken == 1
            if action.is_push:
                assert self.environment.policy.resource_pushed_from(action.push) == action.source
                assert obs["resources"][str(action.push.order)][-2] == action.source.source_id + 1
            if action.is_preload:
                assert self.environment.policy.resource_preloaded_from(action.push) == action.source
                assert obs["resources"][str(action.push.order)][-1] == action.source.order + 1
        finally:
            self.environment.reset()

    def test_observation(self):
        obs = self.environment.observation
        assert obs and isinstance(obs, dict)
        assert self.environment.observation_space.contains(obs)

    def test_obseration_when_environment_is_created_with_dict(self):
        env = Environment(get_config()._asdict())
        obs = env.observation
        assert obs and isinstance(obs, dict)
        assert self.environment.observation_space.contains(obs)

    def test_render(self):
        with pytest.raises(NotImplementedError):
            self.environment.render()

    def test_environment_with_cached_urls(self):
        config = get_config()
        resources = [res for group in config.env_config.push_groups for res in group.resources]
        mask = [random.randint(0, 2) for _ in range(len(resources))]
        cached = [res for (res, include) in zip(resources, mask) if include]
        cached_urls = set(res.url for res in cached)

        config = config.with_mutations(cached_urls=cached_urls)
        env = Environment(config)

        obs = env.observation
        for res in cached:
            assert obs["resources"][str(res.order)][1] == 1
