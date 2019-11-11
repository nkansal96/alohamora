""" This module defines the model for training and instantiating A3C agents """

from statistics import stdev

from blaze.config.config import Config
from blaze.config.train import TrainConfig
from blaze.environment import Environment
from blaze.logger import logger

from .model import SavedModel


WINDOW_SIZE = 50
MAX_ITERATIONS = 400
MIN_ITERATIONS = 100


class StopCondition:
    """
    Implements a stateful stopping condition to automatically stop the training based on analyzing the running
    episode reward mean over a certain window size. It also stop automatically if the number of training iterations
    exceeds some maximum, but not before it exceeds some minimum.
    """

    def __init__(self):
        self.log = logger.with_namespace("stop_condition")
        self.num_iters = 0
        self.episode_max_rewards = []
        self.episode_min_rewards = []
        self.episode_mean_rewards = []

    def __call__(self, trial_id, result):
        self.num_iters += 1

        if "episode_reward_max" in result and "episode_reward_min" in result and "episode_reward_mean" in result:
            self.log.debug("recording trial result", trial_id=trial_id, num_iters=self.num_iters)
            self.episode_max_rewards.append(result["episode_reward_max"])
            self.episode_min_rewards.append(result["episode_reward_min"])
            self.episode_mean_rewards.append(result["episode_reward_mean"])
        else:
            self.log.warn("unable to record episode result", result=result, trial_id=trial_id)
            return False

        # truncate the rewards list to past `WINDOW_SIZE` iterations only
        self.episode_max_rewards = self.episode_max_rewards[-WINDOW_SIZE:]
        self.episode_min_rewards = self.episode_min_rewards[-WINDOW_SIZE:]
        self.episode_mean_rewards = self.episode_mean_rewards[-WINDOW_SIZE:]

        if self.num_iters > MIN_ITERATIONS:
            self.log.debug(
                "reward stats",
                stdev_max=stdev(self.episode_max_rewards),
                stdev_min=stdev(self.episode_min_rewards),
                stdev_mean=stdev(self.episode_mean_rewards),
            )
            relative_stdev_based_stop = stdev(self.episode_mean_rewards) < 0.01 * self.episode_mean_rewards[-1]
            if self.num_iters > MAX_ITERATIONS or relative_stdev_based_stop:
                self.log.info("auto stopping", iters=self.num_iters)
                return True
        return False


COMMON_CONFIG = {
    "sample_batch_size": 256,
    "train_batch_size": 1024,
    "batch_mode": "truncate_episodes",
    "collect_metrics_timeout": 1200,
    "num_workers": 2,
    "num_gpus": 0,
}


def train(train_config: TrainConfig, config: Config):
    """ Trains an A3C agent with the given training and environment configuration """
    # lazy load modules so that they aren't imported if they're not necessary
    import ray
    from ray.tune import run_experiments

    ray.init(num_cpus=train_config.num_cpus, log_to_driver=False)

    name = train_config.experiment_name
    run_experiments(
        {
            name: {
                "run": "A3C",
                "env": Environment,
                "stop": ray.tune.function(StopCondition()),
                "checkpoint_at_end": True,
                "checkpoint_freq": 10,
                "max_failures": 1000,
                "config": {
                    **COMMON_CONFIG,
                    "num_workers": train_config.num_cpus // 2,
                    "env_config": config,
                    # "model": {"custom_action_dist": action_distribution_creator},
                },
            }
        },
        resume=train_config.resume,
    )


def get_model(location: str):
    """ Returns a SavedModel for instantiation given a model checkpoint directory """
    from ray.rllib.agents.a3c import A3CAgent

    return SavedModel(A3CAgent, Environment, location, COMMON_CONFIG)
