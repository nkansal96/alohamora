from typing import Optional

import gym

from blaze.config.client import ClientEnvironment
from blaze.policy import Policy
from .config import Config

def get_observation_space(client_environment: ClientEnvironment, config: Config):
    return {}

def get_observation(client_environment: ClientEnvironment, config: Config, push_policy: Policy):
    return {}
