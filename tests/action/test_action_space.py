from collections import Counter

import gym
import pytest

from blaze.action import Action
from blaze.action.action import NOOP_ACTION_ID, NOOP_PUSH_ACTION_ID, NOOP_PRELOAD_ACTION_ID
from blaze.action.action_space import ActionSpace, PreloadActionSpace, PushActionSpace

from tests.mocks.config import get_push_groups, convert_push_groups_to_push_pairs


def to_tuple(o):
    try:
        return tuple(map(to_tuple, o))
    except TypeError:
        return o


class TestPushActionSpace:
    def setup(self):
        self.push_groups = [group for group in get_push_groups() if group.trainable]
        self.action_space = PushActionSpace(self.push_groups)
        self.action_space.seed(2048)  # for deterministic output

    def test_init(self):
        assert isinstance(self.action_space, gym.spaces.MultiDiscrete)
        assert self.action_space.nvec.shape == (3,)

        max_group_id = max(g.id for g in self.push_groups)
        assert self.action_space.max_group_id == max_group_id
        assert self.action_space.nvec[0] == 1 + max_group_id

        max_source_id = max(r.source_id for g in self.push_groups for r in g.resources)
        assert self.action_space.max_source_id == max_source_id
        assert self.action_space.nvec[1] == 1 + max_source_id
        assert self.action_space.nvec[2] == 1 + max_source_id

        all_source_id = set([r for g, v in self.action_space.group_id_to_source_id.items() for r in v])
        all_resources = set([r for g, v in self.action_space.group_id_to_resource_map.items() for r in v.values()])

        assert all_source_id == set(r.source_id for g in self.push_groups for r in g.resources)
        assert all_resources == set(r for g in self.push_groups for r in g.resources)

    def test_sample_returns_infinitely_when_actions_not_used(self):
        action_space = PushActionSpace(self.push_groups)
        action_space.seed(2048)
        all_actions = []

        for _ in range(50):
            action_id = action_space.sample()
            assert (action_id != NOOP_PUSH_ACTION_ID).any(), "Should not return a NOOP"
            all_actions.append(tuple(action_id))

        # Chances are it returned some pushed object more than once
        counter = Counter((g, p) for (g, _, p) in all_actions)
        assert sum(counter.values()) == 50
        assert len(counter.keys()) < 10
        assert any(v > 1 for v in counter.values()), "Should have returned a pushed object more than once"

        # Chances are it returned some action more than once
        counter = Counter(all_actions)
        assert sum(counter.values()) == 50
        assert len(counter.keys()) < 50
        assert any(v > 1 for v in counter.values()), "Should have returned some action more than once"

    def test_sample_returns_all_push_actions_uniquely_when_used(self):
        action_space = PushActionSpace(self.push_groups)
        action_space.seed(2048)
        assert not action_space.empty()

        all_actions = set()
        for i in range(50):
            action_id = action_space.sample()
            if (action_id == NOOP_PUSH_ACTION_ID).all():
                break
            assert not action_space.empty()
            assert tuple(action_id) not in all_actions
            all_actions.add(tuple(action_id))
            action_space.use_action(action_space.decode_action_id(action_id))
        else:
            # If there was no break, sample did not stop
            assert False, "sample returned too many items"

        assert i == len(all_actions) == sum(len(g.resources) - 1 for g in self.push_groups)
        assert action_space.empty()

    def test_contains(self):
        # Does not contain an action with invalid push group
        assert not self.action_space.contains((5, 0, 1))
        # Does not contain an action with source ID out of bounds of push group
        assert not self.action_space.contains((0, 10, 1))
        # Does not contain an action with push ID out of bounds of push group
        assert not self.action_space.contains((0, 1, 10))
        # Does not contain an action with source ID >= push ID
        assert not self.action_space.contains((0, 1, 1))
        assert not self.action_space.contains((0, 2, 1))

        # Does contain NOOP
        assert self.action_space.contains(NOOP_PUSH_ACTION_ID)

        # Contains all valid push combiniations
        for group in self.push_groups:
            for source in group.resources:
                for push in group.resources:
                    action_id = (group.id, source.source_id, push.source_id)
                    if action_id == tuple(NOOP_PUSH_ACTION_ID):
                        continue
                    if source.source_id < push.source_id:
                        assert self.action_space.contains(action_id)
                    else:
                        assert not self.action_space.contains(action_id)

    def test_decode_fails_for_action_not_in_action_space(self):
        assert self.action_space.decode_action_id(NOOP_PUSH_ACTION_ID).is_noop
        assert self.action_space.decode_action_id((0, 1, 1)).is_noop
        assert self.action_space.decode_action_id((0, 2, 1)).is_noop
        assert self.action_space.decode_action_id((0, 20, 21)).is_noop

    def test_decode_returns_correct_action_for_each_valid_action_id(self):
        for group in self.push_groups:
            for source in group.resources:
                for push in group.resources:
                    action_id = (group.id, source.source_id, push.source_id)
                    action = self.action_space.decode_action_id(action_id)
                    if source.source_id < push.source_id:
                        assert not action.is_noop
                        assert action.is_push
                        assert action.push == push
                        assert action.source == source
                    else:
                        assert action.is_noop

    def test_use_action_noop(self):
        original_push = {k: list(v) for k, v in self.action_space.group_id_to_source_id.items()}
        self.action_space.use_action(Action())
        assert self.action_space.group_id_to_source_id == original_push

        self.action_space.use_action(
            Action(is_push=True, source=self.push_groups[0].resources[0], push=self.push_groups[0].resources[1])
        )
        assert self.action_space.group_id_to_source_id == original_push


class TestPreloadActionSpace:
    def setup(self):
        self.push_groups = get_push_groups()
        self.action_space = PreloadActionSpace(self.push_groups)
        self.action_space.seed(2048)  # for deterministic output
        self.all_resources = set(r for g in self.push_groups for r in g.resources)

    def test_init(self):
        assert isinstance(self.action_space, gym.spaces.MultiDiscrete)
        assert self.action_space.nvec.shape == (2,)

        max_order = max(r.order for r in self.all_resources)

        assert self.action_space.nvec[0] == max_order + 1
        assert self.action_space.nvec[1] == max_order + 1

        assert set(self.action_space.order_to_resource_map.values()) == self.all_resources

        assert 0 not in self.action_space.preload_list
        assert len(self.action_space.preload_list) == len(set(self.action_space.preload_list))
        assert len(self.action_space.preload_list) == len(self.all_resources) - 1

        assert len(self.action_space.source_list) == len(set(self.action_space.source_list))
        assert len(self.action_space.source_list) == len(self.all_resources)
        assert self.action_space.max_order == len(self.all_resources) - 1 == max(r.order for r in self.all_resources)

    def test_sample_returns_infinitely_when_actions_not_used(self):
        action_space = PreloadActionSpace(self.push_groups)
        action_space.seed(2048)
        all_actions = []

        for _ in range(50):
            action_id = action_space.sample()
            assert (action_id != NOOP_PRELOAD_ACTION_ID).any(), "Should not return a NOOP"
            all_actions.append(tuple(action_id))

        # Chances are it returned some preloaded object more than once
        counter = Counter(p for (_, p) in all_actions)
        assert sum(counter.values()) == 50
        assert len(counter.keys()) < 13
        assert any(v > 1 for v in counter.values()), "Should have returned a preloaded object more than once"

        # Chances are it returned some action more than once
        counter = Counter(all_actions)
        assert sum(counter.values()) == 50
        assert len(counter.keys()) < 50
        assert any(v > 1 for v in counter.values()), "Should have returned some action more than once"

    def test_sample_returns_all_preload_actions_uniquely_when_used(self):
        action_space = PreloadActionSpace(self.push_groups)
        action_space.seed(2048)
        assert not action_space.empty()

        all_actions = set()
        for i in range(50):
            action_id = action_space.sample()
            if (action_id == NOOP_PRELOAD_ACTION_ID).all():
                break
            assert not action_space.empty()
            assert tuple(action_id) not in all_actions
            all_actions.add(tuple(action_id))
            action_space.use_action(action_space.decode_action_id(action_id))
        else:
            # If there was no break, sample did not stop
            assert False, "sample returned too many items"

        assert i == len(all_actions) == sum(len(g.resources) for g in self.push_groups) - 1
        assert action_space.empty()

    def test_contains(self):
        # Does not contain an action with source ID out of bounds of push group
        assert not self.action_space.contains((20, 21))
        # Does not contain an action with push ID out of bounds of push group
        assert not self.action_space.contains((0, 21))
        # Does not contain an action with source ID >= push ID
        assert not self.action_space.contains((1, 1))
        assert not self.action_space.contains((2, 1))

        # Does contain NOOP
        assert self.action_space.contains(NOOP_PRELOAD_ACTION_ID)

        # Contains all valid push combiniations
        for source in self.all_resources:
            for preload in self.all_resources:
                action_id = (source.order, preload.order)
                if action_id == tuple(NOOP_PRELOAD_ACTION_ID):
                    continue
                if source.order < preload.order:
                    assert self.action_space.contains(action_id)
                else:
                    assert not self.action_space.contains(action_id)

    def test_decode_fails_for_action_not_in_action_space(self):
        assert self.action_space.decode_action_id(NOOP_PRELOAD_ACTION_ID).is_noop
        assert self.action_space.decode_action_id((1, 1)).is_noop
        assert self.action_space.decode_action_id((2, 1)).is_noop
        assert self.action_space.decode_action_id((20, 21)).is_noop

    def test_decode_returns_correct_action_for_each_valid_action_id(self):
        for source in self.all_resources:
            for preload in self.all_resources:
                action_id = (source.order, preload.order)
                action = self.action_space.decode_action_id(action_id)
                if source.order < preload.order:
                    assert not action.is_noop
                    assert not action.is_push
                    assert action.push == preload
                    assert action.source == source
                else:
                    assert action.is_noop


class TestActionSpace:
    def setup(self):
        self.push_groups = get_push_groups()

    def test_init_raises_when_both_push_and_preload_disabled(self):
        with pytest.raises(AssertionError):
            ActionSpace(self.push_groups, disable_preload=True, disable_push=True)

    def test_init_disabled_push(self):
        action_space = ActionSpace(self.push_groups, disable_push=True)
        assert action_space.disable_push
        assert not action_space.disable_preload

        assert action_space.num_action_types == 2
        assert action_space.action_types == [0, 1]

        assert len(action_space.spaces) == 3
        assert action_space.spaces[0].n == 2
        assert action_space.spaces[1] == action_space.push_space
        assert action_space.spaces[2] == action_space.preload_space

    def test_init_disabled_preload(self):
        action_space = ActionSpace(self.push_groups, disable_preload=True)
        assert not action_space.disable_push
        assert action_space.disable_preload

        assert action_space.num_action_types == 2
        assert action_space.action_types == [0, 1]

        assert len(action_space.spaces) == 3
        assert action_space.spaces[0].n == 2
        assert action_space.spaces[1] == action_space.push_space
        assert action_space.spaces[2] == action_space.preload_space

    def test_sample_returns_infinitely_when_actions_not_used(self):
        action_space = ActionSpace(self.push_groups)
        action_space.seed(10000)
        all_actions = []
        num_iters = 300

        for _ in range(num_iters):
            action_id = action_space.sample()
            action_type, push_action, preload_action = action_id

            if action_type == 0:
                assert to_tuple(action_id) == to_tuple(NOOP_ACTION_ID), "should be a noop"
            if action_type == 1:
                assert to_tuple(push_action) != to_tuple(NOOP_PUSH_ACTION_ID), "push should not be a noop"
                assert to_tuple(preload_action) == to_tuple(NOOP_PRELOAD_ACTION_ID), "preload should be noop"
                assert action_space.push_space.contains(push_action)
            if action_type == 2:
                assert to_tuple(push_action) == to_tuple(NOOP_PUSH_ACTION_ID), "preload should not be noop"
                assert to_tuple(preload_action) != to_tuple(NOOP_PRELOAD_ACTION_ID), "push should be a noop"
                assert action_space.preload_space.contains(preload_action)

            all_actions.append(tuple(action_id))

        # Should return approximately 4-48-48 proportion of each type of action
        action_types = Counter(a for (a, _, _) in all_actions)
        assert (num_iters * 0.04 * 0.90) <= action_types[0] <= (num_iters * 0.04 * 1.1)
        assert (num_iters * 0.48 * 0.95) <= action_types[1] <= (num_iters * 0.48 * 1.05)
        assert (num_iters * 0.48 * 0.95) <= action_types[2] <= (num_iters * 0.48 * 1.05)
        assert sum(action_types.values()) == num_iters == len(all_actions)

    def test_sample_only_push(self):
        action_space = ActionSpace(self.push_groups, disable_preload=True)
        action_space.seed(10000)
        all_actions = []
        num_iters = 150

        for _ in range(num_iters):
            action_id = action_space.sample()
            action_type, push_action, preload_action = action_id

            if action_type == 0:
                assert to_tuple(action_id) == to_tuple(NOOP_ACTION_ID), "should be a noop"
            if action_type == 1:
                assert to_tuple(push_action) != to_tuple(NOOP_PUSH_ACTION_ID), "push should not be a noop"
                assert to_tuple(preload_action) == to_tuple(NOOP_PRELOAD_ACTION_ID), "preload should be noop"
                assert action_space.push_space.contains(push_action)
            if action_type == 2:
                assert False, "action_type == 2 should not be possible"

            all_actions.append(tuple(action_id))

        # Should return approximately 4-96 proportion of each type of action
        action_types = Counter(a for (a, _, _) in all_actions)
        assert (num_iters * 0.04 * 0.8) <= action_types[0] <= (num_iters * 0.04 * 1.2)
        assert (num_iters * 0.96 * 0.95) <= action_types[1] <= (num_iters * 0.96 * 1.05)
        assert sum(action_types.values()) == num_iters == len(all_actions)

    def test_sample_only_preload(self):
        action_space = ActionSpace(self.push_groups, disable_push=True)
        action_space.seed(10000)
        all_actions = []
        num_iters = 150

        for _ in range(num_iters):
            action_id = action_space.sample()
            action_type, push_action, preload_action = action_id

            if action_type == 0:
                assert to_tuple(action_id) == to_tuple(NOOP_ACTION_ID), "should be a noop"
            if action_type == 1:
                assert to_tuple(push_action) == to_tuple(NOOP_PUSH_ACTION_ID), "push should be a noop"
                assert to_tuple(preload_action) != to_tuple(NOOP_PRELOAD_ACTION_ID), "preload should not be noop"
                assert action_space.push_space.contains(push_action)
            if action_type == 2:
                assert False, "action_type == 2 should not be possible"

            all_actions.append(tuple(action_id))

        # Should return approximately 4-96 proportion of each type of action
        action_types = Counter(a for (a, _, _) in all_actions)
        assert (num_iters * 0.04 * 0.8) <= action_types[0] <= (num_iters * 0.04 * 1.2)
        assert (num_iters * 0.96 * 0.95) <= action_types[1] <= (num_iters * 0.96 * 1.05)
        assert sum(action_types.values()) == num_iters == len(all_actions)

    def test_sample_returns_all_actions_uniquely_when_used(self):
        action_space = ActionSpace(self.push_groups, disable_push=True)
        action_space.seed(10000)
        all_actions = []
        num_iters = 150

        assert not action_space.empty()

        all_actions = set()
        for i in range(num_iters):
            action_id = action_space.sample()
            action_type, _, _ = action_id

            if action_type == 0 and action_space.empty():
                break

            assert to_tuple(action_id) not in all_actions
            all_actions.add(to_tuple(action_id))
            action_space.use_action(action_space.decode_action(action_id))
        else:
            # If there was no break, sample did not stop
            assert False, "sample returned too many items"

        assert i == len(all_actions)
        assert action_space.empty()
