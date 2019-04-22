"""
This module defines the classes and methods used to configure Mahimahi shells
"""

import os
from typing import List, Optional

from blaze.action import Policy
from blaze.config import Config
from blaze.config.client import ClientEnvironment
from .trace import format_trace_lines, trace_for_kbps

class MahiMahiConfig():
  """ MahiMahiConfig represents a configuration for some Mahimahi shells """
  def __init__(self, config: Config, policy: Optional[Policy] = None,
               client_environment: Optional[ClientEnvironment] = None):
    self.config = config
    self.policy = policy
    self.client_environment = client_environment

  def proxy_replay_shell_with_cmd(self, push_config_file_name: str, cmd: List[str]) -> List[str]:
    """
    Writes the given push configuration and returns a command that can be run
    to start a link shell and proxy replay shell with the given command
    """
    return [
      *self.proxy_replay_cmd,
      push_config_file_name,
      *self.delay_cmd,
      *self.link_cmd,
      *cmd
    ]

  def record_shell_with_cmd(self, save_dir: str, cmd: List[str]) -> List[str]:
    """
    Returns a command that can be run to start an optional link shell and web
    record shell with the given command
    """
    return [*self.link_cmd, *self.record_cmd(save_dir), *cmd]

  @property
  def link_cmd(self) -> List[str]:
    """
    Returns the Mahimahi link shell command based on the client_environment that
    this class was configured with. If no client_environment is specified, this
    function returns an empty array.
    """
    if self.client_environment is None:
      return []
    trace = format_trace_lines(trace_for_kbps(self.client_environment.bandwidth))
    trace_fmt = '<(echo \'{}\')'.format(trace)
    return ['mm-link', trace_fmt, trace_fmt, '--']

  @property
  def delay_cmd(self) -> List[str]:
    """
    Returns the Mahimahi delay shell command based on the latency specified in the
    client_environment. If the latency is <= 0 or client_environment was not specified,
    then this function returns an empty array
    """
    if self.client_environment is None or self.client_environment.latency <= 0:
      return []
    return ['mm-delay', str(self.client_environment.latency // 2)]

  @property
  def proxy_replay_cmd(self) -> List[str]:
    """
    Returns the Mahimahi proxy replay shell command. It reads from the Config object
    passed in when the MahiMahiConfig object was created for the location of the replay
    directory, the nghttpx binary, and the Mahimahi proxy certificates. This function returns
    an incomplete command: one more argument (the push configuration file path) needs to
    be specified at the end of the list.
    """
    return [
      'mm-proxyreplay',
      self.config.env_config.replay_dir,
      self.config.nghttpx_bin,
      os.path.join(self.config.mahimahi_cert_dir, 'reverse_proxy_key.pem'),
      os.path.join(self.config.mahimahi_cert_dir, 'reverse_proxy_cert.pem'),
    ]

  def record_cmd(self, save_dir: str) -> List[str]:
    """ Returns the command to create a record shell with the given target directory """
    return ['mm-webrecord', save_dir]

  @property
  def formatted_push_policy(self):
    """ Returns the push policy in a format that Mahimahi understands """
    if self.policy is None:
      raise AttributeError('Push policy must be specified in the constructor')
    return '\n'.join([
      '{parent}\t{dependencies}'.format(parent=parent.url, dependencies='\t'.join(dep.url for dep in deps))
      for (parent, deps) in self.policy
    ])
