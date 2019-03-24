import collections
import json

class Policy(object):
  def __init__(self, push_groups, action_space):
    self.push_groups = push_groups
    self.max_urls_in_group = max(len(group['urls']) for group in push_groups)
    self.total_urls = sum(len(group['urls']) for group in push_groups)
    self.actions_taken = 0
    self._push_policy = {
      i: {
        j: {
          k: 0 for k in range(len(push_groups[i]['urls']))
        } for j in range(len(push_groups[i]['urls']))
      } for i in range(len(push_groups))
    }
  
  def __iter__(self):
    return self.observation.items()

  @property
  def observation(self):
    return self._push_policy

  @property
  def completed(self):
    return self.actions_taken >= self.total_urls

  @property
  def push_policy(self):
    policy = collections.defaultdict(list)
    for i, group in self._push_policy.items():
      for j, push in group.items():
        push_urls = [self.push_groups[i]['urls'][k] for k, should_push in push.items() if should_push]
        if len(push_urls) > 0:
          policy[self.push_groups[i]['urls'][j]].extend(push_urls)
    return dict(policy)
  
  def valid_action(self, action):
    return True

  def decode_action(self, action):
    actions_in_group = self.max_urls_in_group * (self.max_urls_in_group + 1)
    group_index = action // actions_in_group
    source = (action - group_index * actions_in_group) // (self.max_urls_in_group + 1)
    push = (action - group_index * actions_in_group - source * (self.max_urls_in_group + 1))
    return group_index, source, push

  def apply_action(self, action):
    group_index, source, push = action
    urls = self.push_groups[group_index]['urls']

    self.actions_taken += 1
    if push == 0:
      return False

    source = source % len(urls)
    if source == len(urls) - 1:
      return False
    push = (push - 1) % len(urls)
    if push < source:
      push = source + 1 + (push % (len(urls) - source - 1))
    if push == source or push >= len(urls):
      return False
    if any(self._push_policy[group_index][s][push] for s in self._push_policy[group_index]):
      return False
    self._push_policy[group_index][source][push] = 1
    return True
