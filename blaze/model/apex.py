""" This module defines the model for training and instantiating APEX agents """

from blaze.config.config import Config
from blaze.config.train import TrainConfig
from blaze.environment import Environment

from .model import SavedModel


COMMON_CONFIG = {
    "sample_batch_size": 128,
    "train_batch_size": 512,
    "batch_mode": "truncate_episodes",
    "collect_metrics_timeout": 1200,
    "num_workers": 2,
    "num_gpus": 0,
}


def train(train_config: TrainConfig, config: Config):
    """ Trains an APEX agent with the given training and environment configuration """
    # lazy load modules so that they aren't imported if they're not necessary
    import ray
    from ray.tune import run_experiments

    ray.init(num_cpus=train_config.num_workers + 1)

    name = train_config.experiment_name
    run_experiments(
        {
            name: {
                "run": "APEX",
                "env": Environment,
                "stop": {"timesteps_total": 1000000},
                "checkpoint_at_end": True,
                "checkpoint_freq": 10,
                "max_failures": 1000,
                "config": {**COMMON_CONFIG, "num_workers": train_config.num_workers, "env_config": config},
            }
        },
        resume=train_config.resume,
    )


def get_model(location: str):
    """ Returns a SavedModel for instantiation given a model checkpoint directory """
    from ray.rllib.agents.dqn import ApexAgent

    return SavedModel(ApexAgent, Environment, location, COMMON_CONFIG)
