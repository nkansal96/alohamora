""" This module defines the model for training and instantiating PPO agents """

from blaze.config.config import Config
from blaze.config.train import TrainConfig
from blaze.environment import Environment

from .model import SavedModel

def train(train_config: TrainConfig, config: Config):
  """ Trains an PPO agent with the given training and environment configuration """
  # lazy load modules so that they aren't imported if they're not necessary
  import ray
  ray.init(num_cpus=train_config.num_cpus)

  name = train_config.experiment_name
  ray.tune.run_experiments({
    name : {
      "run": "PPO",
      "env": Environment,
      "stop": {
        "timesteps_total": train_config.max_timesteps,
      },
      "checkpoint_at_end": True,
      "checkpoint_freq": 1,
      "max_failures": 20,
      "config": {
        "sample_batch_size": 32,
        "train_batch_size": 256,
        "sgd_minibatch_size": 64,
        "collect_metrics_timeout": 1200,
        "num_workers": train_config.num_cpus//2,
        "num_gpus": 0,
        "env_config": config,
      },
    },
  }, resume='prompt')

def get_model(location: str):
  """ Returns a SavedModel for instantiation given a model checkpoint directory """
  from ray.rllib.agents.ppo import PPOAgent
  return SavedModel(PPOAgent, Environment, location)
