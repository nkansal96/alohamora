import itertools

from blaze.action import Action, ActionSpace, Policy

from tests.mocks.config import get_push_groups


class TestPolicy:
    def setup(self):
        self.push_groups = get_push_groups()

    def test_init(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        assert isinstance(policy, Policy)
        assert policy.action_space == action_space

    def test_completed_before_all_actions_used(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        for _ in range(len(action_space) - 1):
            policy.apply_action(action_space.sample())
            assert not policy.completed

    def test_completed_after_all_actions_used(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        while action_space:
            policy.apply_action(action_space.sample())
        assert policy.completed

    def test_completed_if_all_actions_noop(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        for _ in range(len(action_space)):
            policy.apply_action(0)
        assert policy.completed

    def test_apply_action_noop_as_first_action(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        applied = policy.apply_action(0)
        assert not applied  # check that action was not applied
        assert not list(policy)  # check that no URLs were added to the policy
        assert len(policy) == 1  # check that the policy length > 0

    def test_apply_action_noop_as_second_action(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)

        applied = policy.apply_action(1)
        output_policy = list(policy)
        assert applied
        assert output_policy
        assert len(policy) == 1

        applied = policy.apply_action(0)
        assert not applied
        assert output_policy == list(policy)
        assert len(policy) == 2

    def test_apply_action(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)

        action = action_space.decode_action_id(1)
        applied = policy.apply_action(1)
        output_policy = list(policy)
        assert applied
        assert len(policy) == 1
        assert len(output_policy) == 1
        assert len(output_policy[0][1]) == 1
        assert output_policy[0][0] == action.source
        assert output_policy[0][1] == set([action.push])

    def test_apply_action_same_source_resource(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)

        action_1 = action_space.decode_action_id(1)
        action_2 = action_space.decode_action_id(2)
        assert policy.apply_action(1)
        assert policy.apply_action(2)

        output_policy = list(policy)
        assert len(policy) == 2
        assert len(output_policy) == 1
        assert len(output_policy[0][1]) == 2
        assert output_policy[0][0] == action_1.source
        assert output_policy[0][0] == action_2.source
        assert output_policy[0][1] == set([action_1.push, action_2.push])

    def test_apply_multiple_actions(self):
        action_space = ActionSpace(self.push_groups)
        num_push_res = len(action_space)
        policy = Policy(action_space)

        actions = []
        while not policy.completed:
            action_id = action_space.sample()
            policy.apply_action(action_id)

            action = action_space.decode_action_id(action_id)
            if not action.is_noop:
                actions.append(action)

        assert len(policy) == num_push_res
        for action in actions:
            assert any(
                action.source == source and action.push == push for source, push_res in policy for push in push_res
            )

    def test_resource_push_from(self):
        action_space = ActionSpace(self.push_groups)
        policy = Policy(action_space)
        action_id = Action().action_id
        while Action(action_id).is_noop:
            action_id = action_space.sample()
        action = action_space.decode_action_id(action_id)
        assert policy.resource_pushed_from(action.push) is None
        assert policy.apply_action(action_id)
        assert policy.resource_pushed_from(action.push) is action.source
