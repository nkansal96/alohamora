import os
import platform
import subprocess
from typing import List

from blaze.action import ActionSpace, Policy
from blaze.config import Config
from blaze.config.client import get_random_client_environment
from blaze.config.environment import PushGroup, Resource, ResourceType, EnvironmentConfig
from blaze.config.train import TrainConfig
from blaze.mahimahi.mahimahi import MahiMahiConfig

def run_cmd(cmd: List[str]) -> str:
  try:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE)
    proc.check_returncode()
    return str(proc.stdout).strip()
  except subprocess.CalledProcessError:
    return ""

def get_push_groups() -> List[PushGroup]:
  return [
    PushGroup(
      group_name='example.com',
      resources=[
        Resource(url='http://example.com/A', size=1024, order=0, group_id=0, source_id=0, type=ResourceType.IMAGE),
        Resource(url='http://example.com/B', size=1024, order=3, group_id=0, source_id=1, type=ResourceType.IMAGE),
        Resource(url='http://example.com/C', size=1024, order=4, group_id=0, source_id=2, type=ResourceType.IMAGE),
      ],
    ),
    PushGroup(
      group_name='sub.example.com',
      resources=[
        Resource(url='http://sub.example.com/D', size=1024, order=1, group_id=1, source_id=0, type=ResourceType.IMAGE),
        Resource(url='http://sub.example.com/E', size=1024, order=2, group_id=1, source_id=1, type=ResourceType.IMAGE),
      ],
    ),
  ]

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

def get_config() -> Config:
  system = platform.system()
  return Config(
    mahimahi_cert_dir=os.path.join(os.path.dirname(__file__), '../../mahimahi/src/frontend/certs'),
    chrome_har_capturer_bin=os.path.join(os.path.dirname(__file__), '../../third_party/node/node_modules/.bin/chrome-har-capturer'),
    pwmetrics_bin=os.path.join(os.path.dirname(__file__), '../../third_party/node/node_modules/.bin/pwmetrics'),
    nghttpx_bin=run_cmd(['which', 'nghttpx']),
    chrome_bin='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' if system == 'Darwin' else run_cmd(['which', 'google-chrome']),
    train_config=get_env_config()
  )

def get_mahimahi_config() -> MahiMahiConfig:
  return MahiMahiConfig(
    config=get_config(),
    policy=Policy(ActionSpace(get_push_groups())),
    client_environment=get_random_client_environment(),
  )
