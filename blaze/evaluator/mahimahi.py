import collections
import contextlib
import os
import tempfile

from blaze.policy import Policy
from blaze.config.client import ClientEnvironment

MAHIMAHI_CERTS_DIR = "/home/ameesh/push-policy/mahimahi/src/frontend/certs",
NGHTTPX_BIN_PATH   = "/usr/local/bin/nghttpx"

class MahiMahiConfig(object):
  def __init__(self, replay_dir: str, push_policy: Policy, environment: ClientEnvironment):
    self.replay_dir = replay_dir
    self.push_policy = push_policy
    self.environment = environment
  
  def cmd(self, push_config_file_name: str):
    with open(push_config_file_name, 'w') as f:
      f.write(self.formatted_push_policy)
    return [*self.link_cmd, *self.replay_cmd, push_config_file_name]

  @property
  def link_cmd(self):
    # TODO: map environment type, bandwidth, and latency to traces
    # return ["mm-link", uplink_trace, downlink_trace, "--"]
    return []
  
  @property
  def replay_cmd(self, push_config_file: str):
    return [
      "mm-proxyreplay",
      self.replay_dir,
      NGHTTPX_BIN_PATH,
      os.path.join(MAHIMAHI_CERTS_DIR, "reverse_proxy_key.pem"),
      os.path.join(MAHIMAHI_CERTS_DIR, "reverse_proxy_cert.pem"),
    ]
  
  @property
  def formatted_push_policy(self):
    return "\n".join([
      "{parent}\t{dependencies}".format(parent=parent, depedencies="\t".join(deps))
        for (parent, deps) in self.push_policy
    ])
