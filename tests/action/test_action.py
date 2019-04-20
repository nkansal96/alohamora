import collections
import copy
import itertools

from blaze.action import Action, ActionSpace

from tests.mocks.config import get_push_groups, convert_push_groups_to_push_pairs

class TestAction():
  def setup(self):
    self.push_groups = get_push_groups()

  def test_init(self):
    a = Action(0)
    assert isinstance(a, Action)
    a = Action(0, self.push_groups[0].resources[0], self.push_groups[0].resources[1])
    assert isinstance(a, Action)

  def test_source_and_push(self):
    source = self.push_groups[0].resources[0]
    push = self.push_groups[0].resources[2]
    a = Action(2, source, push)
    assert a.source == source
    assert a.push == push

    source = self.push_groups[1].resources[0]
    push = self.push_groups[1].resources[1]
    a = Action(3, source, push)
    assert a.source == source
    assert a.push == push


  def test_noop(self):
    a = Action(0)
    assert a.is_noop

  def test_eq(self):
    a1 = Action(action_id=5)
    a2 = Action(action_id=5)
    a3 = Action(action_id=5, source=self.push_groups[1].resources[0])
    assert a1 == a2 == a3

class TestActionSpace():
  def setup(self):
    self.push_groups = get_push_groups()
    self.action_space = ActionSpace(self.push_groups)
    self.action_space.seed(1024) # for deterministic output
    self.sampled_actions = collections.Counter(self.action_space.sample() for i in range(1000))

  def test_init_push_resources(self):
    # pushable resources are all resources except the first in each group
    push_pairs = convert_push_groups_to_push_pairs(self.push_groups)
    pushable_resources = set(v.url for (k, v) in push_pairs)
    assert len(self.action_space.push_resources) == len(pushable_resources)
    for (i, res) in enumerate(self.action_space.push_resources):
      # skipping the zeroth one (noop) and first one (can't push the first resource)
      assert res.order == i + 2

  def test_init_actions(self):
    push_pairs = convert_push_groups_to_push_pairs(self.push_groups)
    # total pairs of resources and 1 no-op
    assert len(self.action_space.actions) == len(push_pairs) + 1
    # ensure all actions are unique
    assert len(set((action.source.group_id, action.source.source_id, action.push.source_id)
                   for action in self.action_space.actions if not action.is_noop)) == len(push_pairs)
    # ensure all push urls are after the source urls
    assert all(action.push.source_id > action.source.source_id
               for action in self.action_space.actions if not action.is_noop)

  def test_seed(self):
    a = ActionSpace(self.push_groups)
    a.seed(100)

  def test_sample_returns_noop(self):
    assert 0 in self.sampled_actions

  def test_sample_returns_all_actions(self):
    assert len(self.sampled_actions) == len(self.action_space.actions)

  def test_sample_returns_more_earlier_resources(self):
    # map action IDs to actions and their count
    actions = ((self.action_space.decode_action_id(action_id), size)
               for (action_id, size) in self.sampled_actions.items())
    # remove no-ops
    actions = (action for action in actions if not action[0].is_noop)
    # sort them by the order in which the push resources appear
    actions = sorted(actions, key=lambda a: a[0].push.order)
    # group by the push resource
    actions = itertools.groupby(actions, key=lambda a: a[0].push.order)
    # transform from (action_id, [(Action, count), (Action, count), ...])
    #  to (action_id, [count, count, ...])
    actions = itertools.starmap(lambda k, g: (k, map(lambda a: a[1], g)), actions)
    # sum up the counts for each action_id
    actions = itertools.starmap(lambda k, g: (k, sum(g)), actions)
    # get a subscriptable list
    actions = list(actions)
    # for each consecutive pair, ensure that earlier push resources are selected
    #  more often
    for i, j in zip(actions[:-1], actions[1:]):
      assert i[1] > j[1]

  def test_sample_does_not_return_used_push_resource(self):
    action_space = copy.deepcopy(self.action_space)
    limit = len(action_space.push_resources)

    # go through all of the actions, but set a hard limit
    while limit > 0:
      action_id = action_space.sample()
      a = action_space.decode_action_id(action_id)
      action_space.use_action(a)
      if a.is_noop:
        continue
      assert a.push not in action_space.push_resources
      if not action_space:
        break
      limit -= 1
    else:
      assert False, 'Did not cycle through all push resources'

  def test_use_action_noop(self):
    action_space = copy.deepcopy(self.action_space)
    original_len = len(action_space.push_resources)
    action_space.use_action(Action())
    assert len(action_space.push_resources) == original_len

  def test_contains(self):
    for i in range(10):
      action_id = self.action_space.sample()
      assert self.action_space.contains(action_id)
    assert not self.action_space.contains(-1)
    assert not self.action_space.contains(len(self.action_space.actions))
