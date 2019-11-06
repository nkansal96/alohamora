import collections
import copy
import itertools

from blaze.action import Action
from blaze.action.action import NOOP_PUSH_ACTION_ID

from tests.mocks.config import get_push_groups


class TestAction:
    def setup(self):
        self.push_groups = get_push_groups()
        self.push_action_id = (1, 1, 2)
        self.preload_action_id = (1, 2)

    def test_init(self):
        a = Action()
        assert isinstance(a, Action)
        a = Action(
            NOOP_PUSH_ACTION_ID,
            is_push=True,
            source=self.push_groups[0].resources[0],
            push=self.push_groups[0].resources[1],
        )
        assert isinstance(a, Action)

    def test_source_and_push(self):
        source = self.push_groups[0].resources[0]
        push = self.push_groups[0].resources[2]
        a = Action(self.push_action_id, is_push=True, source=source, push=push)
        assert a.source == source
        assert a.push == push

        source = self.push_groups[1].resources[0]
        push = self.push_groups[1].resources[1]
        a = Action(self.push_action_id, is_push=True, source=source, push=push)
        assert a.source == source
        assert a.push == push

    def test_preload(self):
        source = self.push_groups[0].resources[0]
        push = self.push_groups[0].resources[2]
        a = Action(self.push_action_id, is_push=True, source=source, push=push)
        assert a.is_push
        assert not a.is_preload

        a = Action(self.preload_action_id, is_push=False, source=source, push=push)
        assert not a.is_push
        assert a.is_preload

    def test_noop(self):
        a = Action(self.push_action_id)
        assert not a.is_noop
        a = Action()
        assert a.is_noop

    def test_eq(self):
        a1 = Action(self.push_action_id)
        a2 = Action(self.push_action_id)
        a3 = Action(self.push_action_id, source=self.push_groups[1].resources[0])
        assert a1 == a2 == a3
