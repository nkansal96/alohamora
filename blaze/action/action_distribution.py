import functools

import gym

from ray.rllib.models.tf.tf_action_dist import MultiActionDistribution
from ray.rllib.models.catalog import ModelCatalog
from ray.rllib.policy.policy import TupleActions


def action_distribution_creator(action_space: gym.spaces.Tuple, config: dict):
    action_dists = [ModelCatalog.get_action_dist(space, config) for space in action_space.spaces]
    child_dist, input_lens = zip(*action_dists)
    return functools.partial(
        ActionDistribution, action_space=action_space, child_distributions=child_dist, input_lens=input_lens
    )


class ActionDistribution(MultiActionDistribution):
    def __init__(self, inputs, model, action_space, child_distributions, input_lens):
        self.action_space = action_space
        super().__init__(inputs, model, action_space, child_distributions, input_lens)

    def sample(self):
        return TupleActions(list(self.action_space.sample()))
