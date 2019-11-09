import collections
import itertools

from blaze.action import Action, ActionSpace, Policy
from blaze.config.environment import Resource

from tests.mocks.config import get_push_groups


def get_action_space():
    action_space = ActionSpace(get_push_groups())
    action_space.seed(2048)
    return action_space


class TestPolicy:
    def setup(self):
        self.push_groups = get_push_groups()

    def test_init(self):
        action_space = get_action_space()
        policy = Policy(action_space)
        assert isinstance(policy, Policy)
        assert policy.action_space == action_space

    def test_as_dict(self):
        action_space = get_action_space()
        policy = Policy(action_space)
        for _ in range(10):
            action = action_space.decode_action(action_space.sample())
            policy.apply_action(action)
            action_space.use_action(action)

        policy_dict = policy.as_dict
        for (source, push) in policy.push:
            assert all(p.url in [pp["url"] for pp in policy_dict["push"][source.url]] for p in push)
        for (source, preload) in policy.preload:
            assert all(p.url in [pp["url"] for pp in policy_dict["preload"][source.url]] for p in preload)

    def test_apply_action_noop_as_first_action(self):
        action_space = get_action_space()
        policy = Policy(action_space)
        applied = policy.apply_action(Action())
        assert not applied  # check that action was not applied
        assert not list(policy.push)  # check that no URLs were added to the policy
        assert not list(policy.preload)  # check that no URLs were added to the policy
        assert len(policy) == 0  # check that the policy length == 0

    def test_apply_action_noop_as_second_action(self):
        action_space = get_action_space()
        policy = Policy(action_space)

        applied = policy.apply_action((1, (0, 0, 1), (0, 0)))
        output_policy = list(policy.push)
        assert applied
        assert output_policy
        assert len(policy) == 1

        applied = policy.apply_action(Action())
        assert not applied
        assert output_policy == list(policy.push)
        assert len(policy) == 1

    def test_apply_push_action(self):
        action_space = get_action_space()
        policy = Policy(action_space)

        action = action_space.decode_action((1, (0, 0, 1), (0, 0)))
        applied = policy.apply_action((1, (0, 0, 1), (0, 0)))
        output_policy = list(policy.push)
        assert applied
        assert len(policy) == 1
        assert len(output_policy) == 1
        assert len(output_policy[0][1]) == 1
        assert output_policy[0][0] == action.source
        assert output_policy[0][1] == {action.push}

    def test_apply_push_action_same_source_resource(self):
        action_space = get_action_space()
        policy = Policy(action_space)

        action_1 = action_space.decode_action((1, (0, 0, 1), (0, 0)))
        action_2 = action_space.decode_action((1, (0, 0, 2), (0, 0)))
        assert policy.apply_action(action_1)
        assert policy.apply_action(action_2)

        output_policy = list(policy.push)
        assert len(policy) == 2
        assert len(output_policy) == 1
        assert len(output_policy[0][1]) == 2
        assert output_policy[0][0] == action_1.source
        assert output_policy[0][0] == action_2.source
        assert output_policy[0][1] == {action_1.push, action_2.push}

    def test_apply_multiple_actions(self):
        action_space = get_action_space()
        policy = Policy(action_space)

        actions = []
        while len(policy) < 10:
            action_id = action_space.sample()
            action = action_space.decode_action(action_id)
            action_applied = policy.apply_action(action)
            action_space.use_action(action)

            if action_applied:
                actions.append(action)
                action_space.use_action(action)

        for action in actions:
            print(action)
            assert any(
                action.source == source and action.push == push for source, res in policy.push for push in res
            ) or any(action.source == source and action.push == push for source, res in policy.preload for push in res)

    def test_push_preload_list_for_source(self):
        action_space = get_action_space()
        policy = Policy(action_space)

        push_map = collections.defaultdict(set)
        preload_map = collections.defaultdict(set)

        while len(policy) < 10:
            action_id = action_space.sample()
            action = action_space.decode_action(action_id)
            action_applied = policy.apply_action(action)

            if action_applied:
                if action.is_push:
                    push_map[action.source].add(action.push)
                if action.is_preload:
                    preload_map[action.source].add(action.push)

        assert push_map
        assert preload_map
        for (source, push_set) in push_map.items():
            assert policy.push_set_for_resource(source) == push_set
        for (source, preload_set) in preload_map.items():
            assert policy.preload_set_for_resource(source) == preload_set

    def test_resource_push_from(self):
        action_space = get_action_space()
        policy = Policy(action_space)
        action = Action()
        while action.is_noop or not action.is_push:
            action = action_space.decode_action(action_space.sample())
        assert policy.resource_pushed_from(action.push) is None
        assert policy.apply_action(action)
        assert policy.resource_pushed_from(action.push) is action.source

        while action.is_noop or action.is_push:
            action = action_space.decode_action(action_space.sample())
        assert policy.resource_preloaded_from(action.push) is None
        assert policy.apply_action(action)
        assert policy.resource_preloaded_from(action.push) is action.source

    def test_from_dict(self):
        policy_dict = {
            "push": {"A": [{"url": "B", "type": "SCRIPT"}, {"url": "C", "type": "IMAGE"}]},
            "preload": {
                "B": [{"url": "D", "type": "IMAGE"}],
                "G": [{"url": "E", "type": "CSS"}, {"url": "F", "type": "FONT"}],
            },
        }
        policy = Policy.from_dict(policy_dict)
        assert policy.total_actions == 0
        assert not policy.action_space
        for (source, deps) in policy.push:
            assert isinstance(source, Resource)
            assert all(isinstance(push, Resource) for push in deps)
            assert [p["url"] for p in policy_dict["push"][source.url]] == sorted([push.url for push in deps])
            for push in deps:
                assert policy.push_to_source[push] == source
                assert push.url in [p["url"] for p in policy_dict["push"][source.url]]

        for (source, deps) in policy.preload:
            assert isinstance(source, Resource)
            assert all(isinstance(push, Resource) for push in deps)
            assert [p["url"] for p in policy_dict["preload"][source.url]] == sorted([push.url for push in deps])
            for push in deps:
                assert policy.preload_to_source[push] == source
                assert push.url in [p["url"] for p in policy_dict["preload"][source.url]]

        assert len(policy.source_to_push) == len(policy_dict["push"])
        assert len(policy.source_to_preload) == len(policy_dict["preload"])
