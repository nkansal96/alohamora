from typing import List

from blaze.action import ActionSpace, Policy
from blaze.config import Config
from blaze.config.client import get_random_client_environment
from blaze.config.train import PushGroup, Resource, ResourceType, TrainConfig
from blaze.mahimahi.mahimahi import MahiMahiConfig

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
      group_name='cdn.example.com',
      resources=[
        Resource(url='http://cdn.example.com/D', size=1024, order=1, group_id=1, source_id=0, type=ResourceType.IMAGE),
        Resource(url='http://cdn.example.com/E', size=1024, order=2, group_id=1, source_id=1, type=ResourceType.IMAGE),
      ],
    ),
  ]

def get_train_config() -> TrainConfig:
  return TrainConfig(
    replay_dir='/tmp/replay_dir',
    request_url='http://example.com/',
    push_groups=get_push_groups(),
  )

def get_config() -> Config:
  # TODO: these paths might need to be fixed
  return Config(
    mahimahi_cert_dir='/tmp/certs',
    chrome_har_capturer_bin='third_party/node/node_modules/.bin/chrome-har-capturer',
    pwmetrics_bin='third_party/node/node_modules/.bin/pwmetrics',
    nghttpx_bin='/tmp/nghttpx',
    chrome_bin='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    train_config=get_train_config()
  )

def get_mahimahi_config() -> MahiMahiConfig:
  return MahiMahiConfig(
    config=get_config(),
    policy=Policy(ActionSpace(get_push_groups())),
    client_environment=get_random_client_environment(),
  )
