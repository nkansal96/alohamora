""" This module defines the model for training and instantiating A3C agents """

from collections import deque
from statistics import stdev

from blaze.config.config import Config
from blaze.config.train import TrainConfig
from blaze.environment import Environment
from blaze.logger import logger

from .model import SavedModel


WINDOW_SIZE = 50
MAX_ITERATIONS = 250
MIN_ITERATIONS = 50
MAX_TIME_SECONDS = 2 * 60 * 60  # 2 hours


def stop_condition():
    """
    Implements a stateful stopping condition to automatically stop the training based on analyzing the running
    episode reward mean over a certain window size. It also stop automatically if the number of training iterations
    exceeds some maximum, but not before it exceeds some minimum.
    """

    log = logger.with_namespace("stop_condition")
    num_iters = 0
    past_rewards = deque()

    def stopper(trial_id, result):
        nonlocal num_iters, past_rewards
        num_iters += 1

        if "time_since_restore" in result and result["time_since_restore"] >= MAX_TIME_SECONDS:
            log.info("auto stopping", time_seconds=result["time_since_restore"], iters=num_iters)
            return True

        if "episode_reward_max" in result and "episode_reward_min" in result and "episode_reward_mean" in result:
            rewards = (result["episode_reward_min"], result["episode_reward_mean"], result["episode_reward_max"])
            log.debug("recording trial result", trial_id=trial_id, num_iters=num_iters, rewards=rewards)
            past_rewards.append(rewards)
        else:
            log.warn("unable to record episode result", result=result, trial_id=trial_id)
            return False

        # truncate the rewards list to past `WINDOW_SIZE` iterations only
        if len(past_rewards) > WINDOW_SIZE:
            past_rewards.popleft()

        if num_iters > MIN_ITERATIONS:
            stdev_min, stdev_mean, stdev_max = tuple(map(stdev, zip(*past_rewards)))
            log.debug("reward stats", stdev_min=stdev_min, stdev_mean=stdev_mean, stdev_max=stdev_max)
            relative_stdev_based_stop = stdev_mean <= 0.075 * abs(past_rewards[-1][1])

            if num_iters > MAX_ITERATIONS or relative_stdev_based_stop:
                log.info("auto stopping", time_seconds=result.get("time_since_restore", 0), iters=num_iters)
                return True

        return False

    stopper.past_rewards = past_rewards
    return stopper


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

    ray.init(num_cpus=train_config.num_workers + 1, log_to_driver=False)

    name = train_config.experiment_name
    run_experiments(
        {
            name: {
                "run": "A3C",
                "env": Environment,
                "stop": ray.tune.function(stop_condition()),
                "checkpoint_at_end": True,
                "checkpoint_freq": 10,
                "max_failures": 3,
                "config": {
                    **COMMON_CONFIG,
                    "num_workers": train_config.num_workers,
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
