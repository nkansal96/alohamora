""" This module defines the model for training and instantiating APEX agents """

from blaze.config.config import Config
from blaze.config.train import TrainConfig
from blaze.environment import Environment

from .model import SavedModel

def train(train_config: TrainConfig, config: Config):
  """ Trains an APEX agent with the given training and environment configuration """
  # lazy load modules so that they aren't imported if they're not necessary
  import ray
  ray.init(num_cpus=train_config.num_cpus)

  name = train_config.experiment_name
  total_urls = sum(len(group.resources) for group in config.env_config.push_groups)
  ray.tune.run_experiments({
    name : {
      "run": "APEX",
      "env": Environment,
      "stop": {
        "timesteps_total": train_config.max_timesteps,
      },
      "checkpoint_at_end": True,
      "checkpoint_freq": 1,
      "max_failures": 1000,
      "config": {
        "sample_batch_size": 50,
        "train_batch_size": 512,
        "timesteps_per_iteration": total_urls,
        "target_network_update_freq": total_urls * 5,
        "batch_mode": "complete_episodes",
        "collect_metrics_timeout": 1200,
        "num_workers": train_config.num_cpus//2,
        "num_gpus": 0,
        "env_config": config,
      },
    },
  }, resume=train_config.resume)

def get_model(location: str):
  """ Returns a SavedModel for instantiation given a model checkpoint directory """
  from ray.rllib.agents.dqn import ApexAgent
  return SavedModel(ApexAgent, Environment, location)
