from typing import List, Tuple

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.config.config import Config, get_config as _get_config
from blaze.config.environment import PushGroup, Resource, ResourceType, EnvironmentConfig
from blaze.config.serve import ServeConfig
from blaze.config.train import TrainConfig
from blaze.mahimahi.mahimahi import MahiMahiConfig

def get_push_groups() -> List[PushGroup]:
  return [
    PushGroup(
      group_name='example.com',
      resources=[
        Resource(url='http://example.com/A', size=1024, order=0, group_id=0, source_id=0, type=ResourceType.IMAGE),
        Resource(url='http://example.com/B', size=1024, order=3, group_id=0, source_id=1, type=ResourceType.IMAGE),
        Resource(url='http://example.com/C', size=1024, order=4, group_id=0, source_id=2, type=ResourceType.IMAGE),
        Resource(url='http://example.com/F', size=1024, order=6, group_id=0, source_id=3, type=ResourceType.IMAGE),
      ],
    ),
    PushGroup(
      group_name='sub.example.com',
      resources=[
        Resource(url='http://sub.example.com/D', size=1024, order=1, group_id=1, source_id=0, type=ResourceType.IMAGE),
        Resource(url='http://sub.example.com/E', size=1024, order=2, group_id=1, source_id=1, type=ResourceType.IMAGE),
        Resource(url='http://sub.example.com/G', size=1024, order=5, group_id=1, source_id=2, type=ResourceType.IMAGE),
      ],
    ),
  ]

def convert_push_groups_to_push_pairs(push_groups: List[PushGroup]) -> List[Tuple[Resource, Resource]]:
  return [(group.resources[s], group.resources[p])
          for group in push_groups
          for s in range(len(group.resources))
          for p in range(s+1, len(group.resources))]

def get_env_config() -> EnvironmentConfig:
  return EnvironmentConfig(
    replay_dir='/tmp/replay_dir',
    request_url='http://example.com/',
    push_groups=get_push_groups(),
  )

def get_train_config() -> TrainConfig:
  return TrainConfig(
    experiment_name='test',
    model_dir='/tmp/test',
    num_cpus=4,
    max_timesteps=10,
  )

def get_serve_config() -> ServeConfig:
  return ServeConfig(
    host="0.0.0.0",
    port=41568,
    max_workers=1,
  )

def get_config() -> Config:
  return Config(**{**_get_config()._asdict(), 'env_config': get_env_config()})

def get_mahimahi_config() -> MahiMahiConfig:
  return MahiMahiConfig(
    config=get_config(),
    policy=Policy(ActionSpace(get_push_groups())),
    client_environment=get_random_client_environment(),
  )
