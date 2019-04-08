import random
import pytest

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment, network_to_bandwidth_range, \
                                network_to_latency_range, device_speed_to_cpu_slowdown, \
                                ClientEnvironment, NetworkType, NetworkSpeed, DeviceSpeed
from blaze.mahimahi.mahimahi import MahiMahiConfig

from tests.mocks.config import get_config, get_push_groups

class TestMahiMahiConfig():
  def setup(self):
    self.config = get_config()
    self.action_space = ActionSpace(get_push_groups())
    self.client_environment = get_random_client_environment()
    self.policy = Policy(self.action_space)
    while not self.policy.completed:
      self.policy.apply_action(self.action_space.sample())

  def test_init_without_policy(self):
    mm_config = MahiMahiConfig(self.config)
    assert isinstance(mm_config, MahiMahiConfig)
    assert mm_config.policy is None
    assert mm_config.client_environment is None

  def test_init_without_client_environment(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    assert isinstance(mm_config, MahiMahiConfig)
    assert mm_config.policy is self.policy
    assert mm_config.client_environment is None

  def test_init_with_client_environment(self):
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    assert isinstance(mm_config, MahiMahiConfig)
    assert mm_config.policy is self.policy
    assert mm_config.client_environment is self.client_environment

  def test_proxy_replay_shell_with_cmd(self):
    push_config_file_name = '/tmp/push_config'
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    shell_cmd = ['some', 'command']
    cmd = mm_config.proxy_replay_shell_with_cmd(push_config_file_name, shell_cmd)

    assert cmd == (
      mm_config.delay_cmd +
      mm_config.link_cmd +
      mm_config.proxy_replay_cmd +
      [push_config_file_name] +
      shell_cmd
    )

  def test_record_shell_with_cmd(self):
    save_dir = '/tmp/save_dir'
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    cmd = mm_config.record_shell_with_cmd(save_dir, ['a', 'command'])
    assert cmd == (mm_config.link_cmd + mm_config.record_cmd(save_dir) + ['a', 'command'])

  def test_link_cmd_without_environment(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    assert not mm_config.link_cmd

  def test_link_cmd_with_environment(self):
    def test_link_cmd(network_type: NetworkType, network_speed: NetworkSpeed, device_speed: DeviceSpeed):
      bandwidth = random.randint(*network_to_bandwidth_range(network_type, network_speed))
      latency = random.randint(*network_to_latency_range(network_type))
      cpu_slowdown = device_speed_to_cpu_slowdown(device_speed)
      env = ClientEnvironment(network_type, network_speed, device_speed, bandwidth, latency, cpu_slowdown)
      link_cmd = MahiMahiConfig(self.config, self.policy, env).link_cmd
      return (
        link_cmd[0] == 'mm-link' and
        link_cmd[1].startswith('<(echo \'') and
        link_cmd[2] == link_cmd[1] and
        link_cmd[3] == '--'
      )

    assert all(test_link_cmd(nt, ns, ds)
               for nt in list(NetworkType)
               for ns in list(NetworkSpeed)
               for ds in list(DeviceSpeed))

  def test_delay_cmd_without_environment(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    assert not mm_config.delay_cmd

  def test_delay_cmd_with_no_latency(self):
    env = ClientEnvironment(**{**self.client_environment._asdict(), 'latency': 0})
    mm_config = MahiMahiConfig(self.config, self.policy, env)
    assert not mm_config.delay_cmd

    env = ClientEnvironment(**{**self.client_environment._asdict(), 'latency': -1})
    mm_config = MahiMahiConfig(self.config, self.policy, env)
    assert not mm_config.delay_cmd

  def test_delay_cmd(self):
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    delay_cmd = mm_config.delay_cmd
    assert delay_cmd[0] == 'mm-delay'
    assert delay_cmd[1] == str(self.client_environment.latency // 2)

  def test_proxy_replay_cmd(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    proxy_replay_cmd = mm_config.proxy_replay_cmd
    assert proxy_replay_cmd[0] == 'mm-proxyreplay'
    assert proxy_replay_cmd[1] == self.config.train_config.replay_dir
    assert proxy_replay_cmd[2] == self.config.nghttpx_bin
    assert proxy_replay_cmd[3].startswith(self.config.mahimahi_cert_dir)
    assert proxy_replay_cmd[3].endswith('reverse_proxy_key.pem')
    assert proxy_replay_cmd[4].startswith(self.config.mahimahi_cert_dir)
    assert proxy_replay_cmd[4].endswith('reverse_proxy_cert.pem')

  def test_record_cmd(self):
    save_dir = '/tmp/save_dir'
    mm_config = MahiMahiConfig(self.config)
    record_cmd = mm_config.record_cmd(save_dir)
    assert record_cmd[0] == 'mm-webrecord'
    assert record_cmd[1] == save_dir

  def test_formatted_push_policy_without_policy(self):
    mm_config = MahiMahiConfig(self.config)
    with pytest.raises(AttributeError):
      _ = mm_config.formatted_push_policy

  def test_formatted_push_policy_has_all_dependencies(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    formatted_push_policy = mm_config.formatted_push_policy
    print(formatted_push_policy)
    for (parent, deps) in self.policy:
      assert parent.url in formatted_push_policy
      assert all(dep.url in formatted_push_policy for dep in deps)
