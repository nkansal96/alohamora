import random

import gym
import numpy as np

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.environment.observation import get_observation, get_observation_space, MAX_RESOURCES

from tests.mocks.config import get_push_groups


class TestGetObservationSpace:
    def test_get_observation_space(self):
        space = get_observation_space()
        assert isinstance(space, gym.spaces.Dict)


class TestGetObservation:
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
        assert obs["client"]["network_type"] == self.client_environment.network_type.value
        assert obs["client"]["device_speed"] == self.client_environment.device_speed.value

        # assert that all resources are not pushed initially
        assert all(res[-2] == 0 for res in obs["resources"].values())
        # assert that all resources are not preloaded initially
        assert all(res[-1] == 0 for res in obs["resources"].values())

        # assert that the push_groups are encoded correctly
        for group in self.push_groups:
            for res in group.resources:
                assert np.array_equal(
                    obs["resources"][str(res.order)],
                    np.array(
                        (
                            1,  # resource is enabled
                            group.id,  # the resource's domain id
                            res.source_id,  # the resource's relative offset from its domain top
                            res.order + 1,  # the resource's absolute offset from the start of the page load
                            res.type.value,  # resource type
                            res.size // 1000,  # resource size in KB
                            0,  # not pushed
                            0,  # not preloaded
                        )
                    ),
                )

        max_order = max(r.order for group in self.push_groups for r in group.resources)
        for i in range(max_order + 1, MAX_RESOURCES):
            assert np.array_equal(obs["resources"][str(i)], np.array([0, 0, 0, 0, 0, 0, 0, 0]))

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
            for (source, push) in policy.push:
                for push_res in push:
                    # +1 since we have defined it that way
                    assert obs["resources"][str(push_res.order)][-2] == source.source_id + 1

            # make sure the push sources are recorded correctly
            for (source, preload) in policy.preload:
                for push_res in preload:
                    # +1 since we have defined it that way
                    assert obs["resources"][str(push_res.order)][-1] == source.order + 1

            # check that all other resources are not pushed
            pushed_res = set(push_res.order for (source, push) in policy.push for push_res in push)
            preloaded_res = set(push_res.order for (source, push) in policy.preload for push_res in push)
            assert all(res[-2] == 0 for order, res in obs["resources"].items() if int(order) not in pushed_res)
            assert all(res[-1] == 0 for order, res in obs["resources"].items() if int(order) not in preloaded_res)

    def test_observation_with_nonempty_policy_with_default_actions(self):
        # use all push groups except the chosen default group
        candidate_push_groups = [
            i for i, group in enumerate(self.push_groups) if len(group.resources) > 2 and not group.trainable
        ]
        default_group_idx = random.choice(candidate_push_groups)
        default_group = self.push_groups[default_group_idx]
        remaining_groups = [group for i, group in enumerate(self.push_groups) if i != default_group_idx]
        action_space = ActionSpace(remaining_groups)
        policy = Policy(action_space)

        # apply some default action
        for push in default_group.resources[1:]:
            policy.add_default_push_action(default_group.resources[0], push)

        # do some actions and check the observation space over time
        for _ in range(len(action_space) - 1):
            # get an action and apply it in the policy
            action_id = action_space.sample()
            policy.apply_action(action_id)

            # get the observation
            obs = get_observation(self.client_environment, self.push_groups, policy)
            assert self.observation_space.contains(obs)

            # make sure the push sources are recorded correctly
            for (source, push) in policy.observable_push:
                for push_res in push:
                    # +1 since we have defined it that way
                    assert obs["resources"][str(push_res.order)][-2] == source.source_id + 1

            # make sure the push sources are recorded correctly
            for (source, preload) in policy.observable_preload:
                for push_res in preload:
                    # +1 since we have defined it that way
                    assert obs["resources"][str(push_res.order)][-1] == source.order + 1

            # check that all other resources are not pushed
            pushed_res = set(push_res.order for (source, push) in policy.observable_push for push_res in push)
            preloaded_res = set(push_res.order for (source, push) in policy.observable_preload for push_res in push)
            assert all(res[-2] == 0 for order, res in obs["resources"].items() if int(order) not in pushed_res)
            assert all(res[-1] == 0 for order, res in obs["resources"].items() if int(order) not in preloaded_res)
