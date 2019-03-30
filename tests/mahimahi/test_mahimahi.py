import pytest
from unittest import mock

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment, ClientEnvironment, NetworkType, NetworkBandwidth, NetworkLatency, DeviceSpeed
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

  def test_set_push_config_file_name(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    assert mm_config.push_config_file_name is None

    push_config_file_name = '/tmp/push_config'
    mm_config.set_push_config_file_name(push_config_file_name)
    assert mm_config.push_config_file_name == push_config_file_name

  def test_proxy_replay_shell_with_cmd_without_push_config_file(self):
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    with pytest.raises(AttributeError):
      mm_config.proxy_replay_shell_with_cmd([])

  @mock.patch('builtins.open', new_callable=mock.mock_open)
  def test_proxy_replay_shell_with_cmd(self, mock_open):
    push_config_file_name = '/tmp/push_config'
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    mm_config.set_push_config_file_name(push_config_file_name)
    cmd = mm_config.proxy_replay_shell_with_cmd(['a', 'command'])

    assert len(mock_open.call_args_list) == 1
    assert mock_open.call_args[0][0] == push_config_file_name
    assert mock_open.call_args[0][1] == 'w'
    assert mock_open.return_value.write.call_args[0][0] == mm_config.formatted_push_policy
    assert cmd == (mm_config.link_cmd + mm_config.proxy_replay_cmd + ['a', 'command'])

  def test_record_shell_with_cmd(self):
    save_dir = '/tmp/save_dir'
    mm_config = MahiMahiConfig(self.config, self.policy, self.client_environment)
    cmd = mm_config.record_shell_with_cmd(save_dir, ['a', 'command'])
    assert cmd == (mm_config.link_cmd + mm_config.record_cmd(save_dir) + ['a', 'command'])

  def test_link_cmd_without_environment(self):
    mm_config = MahiMahiConfig(self.config, self.policy)
    assert not mm_config.link_cmd

  def test_link_cmd_with_environment(self):
    test_link_cmd = lambda env: MahiMahiConfig(self.config, self.policy, env).link_cmd
    assert all(test_link_cmd(ClientEnvironment(nt, nb, nl, ds))
               for nt in list(NetworkType)
               for nb in list(NetworkBandwidth)
               for nl in list(NetworkLatency)
               for ds in list(DeviceSpeed))

  def test_proxy_replay_cmd(self):
    push_config_file_name = '/tmp/push_config'
    mm_config = MahiMahiConfig(self.config, self.policy)
    mm_config.set_push_config_file_name(push_config_file_name)
    proxy_replay_cmd = mm_config.proxy_replay_cmd
    assert proxy_replay_cmd[0] == 'mm-proxyreplay'
    assert proxy_replay_cmd[1] == self.config.train_config.replay_dir
    assert proxy_replay_cmd[2] == self.config.nghttpx_bin
    assert proxy_replay_cmd[3].startswith(self.config.mahimahi_cert_dir)
    assert proxy_replay_cmd[3].endswith('reverse_proxy_key.pem')
    assert proxy_replay_cmd[4].startswith(self.config.mahimahi_cert_dir)
    assert proxy_replay_cmd[4].endswith('reverse_proxy_cert.pem')
    assert proxy_replay_cmd[5] == push_config_file_name

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
