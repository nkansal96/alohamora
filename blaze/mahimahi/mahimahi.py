import os
from typing import List, Optional

from blaze.action import Policy
from blaze.config import Config
from blaze.config.client import ClientEnvironment

class MahiMahiConfig():
  def __init__(self, config: Config, policy: Optional[Policy] = None,
               client_environment: Optional[ClientEnvironment] = None):
    self.config = config
    self.policy = policy
    self.client_environment = client_environment
    self.push_config_file_name = None

  def set_push_config_file_name(self, file_name):
    self.push_config_file_name = file_name

  def proxy_replay_shell_with_cmd(self, cmd: List[str]):
    if not self.push_config_file_name:
      raise AttributeError('Push config file must be specified with set_push_config_file_name')
    with open(self.push_config_file_name, 'w') as f:
      f.write(self.formatted_push_policy)
    return [*self.link_cmd, *self.proxy_replay_cmd, *cmd]

  def record_shell_with_cmd(self, save_dir: str, cmd: List[str]):
    return [*self.link_cmd, *self.record_cmd(save_dir), *cmd]

  @property
  def link_cmd(self):
    if self.client_environment is None:
      return []
    # TODO: map self.client_environment to traces
    uplink_trace = 'test'
    downlink_trace = 'test'
    return ['mm-link', uplink_trace, downlink_trace, '--']

  @property
  def proxy_replay_cmd(self):
    return [
      'mm-proxyreplay',
      self.config.train_config.replay_dir,
      self.config.nghttpx_bin,
      os.path.join(self.config.mahimahi_cert_dir, 'reverse_proxy_key.pem'),
      os.path.join(self.config.mahimahi_cert_dir, 'reverse_proxy_cert.pem'),
      self.push_config_file_name
    ]

  def record_cmd(self, save_dir: str):
    return ['mm-webrecord', save_dir]

  @property
  def formatted_push_policy(self):
    if self.policy is None:
      raise AttributeError('Push policy must be specified in the constructor')
    return '\n'.join([
      '{parent}\t{dependencies}'.format(parent=parent.url, dependencies='\t'.join(dep.url for dep in deps))
      for (parent, deps) in self.policy
    ])
