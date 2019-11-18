from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.mahimahi.mahimahi import MahiMahiConfig
from blaze.mahimahi.trace import format_trace_lines, trace_for_kbps

from tests.mocks.config import get_config, get_push_groups


class TestMahiMahiConfig:
    def setup(self):
        self.config = get_config()
        self.action_space = ActionSpace(get_push_groups())
        self.client_environment = get_random_client_environment()
        self.policy = Policy(self.action_space)
        applied = True
        while applied:
            applied = self.policy.apply_action(self.action_space.sample())

    def test_init_without_policy(self):
        mm_config = MahiMahiConfig(self.config)
        assert isinstance(mm_config, MahiMahiConfig)
        assert mm_config.policy is None
        assert mm_config.client_environment is None

    def test_init_without_client_environment(self):
        mm_config = MahiMahiConfig(self.config, policy=self.policy)
        assert isinstance(mm_config, MahiMahiConfig)
        assert mm_config.policy is self.policy
        assert mm_config.client_environment is None

    def test_init_with_client_environment(self):
        mm_config = MahiMahiConfig(self.config, policy=self.policy, client_environment=self.client_environment)
        assert isinstance(mm_config, MahiMahiConfig)
        assert mm_config.policy is self.policy
        assert mm_config.client_environment is self.client_environment

    def test_record_shell_with_cmd(self):
        save_dir = "/tmp/save_dir"
        mm_config = MahiMahiConfig(self.config, policy=self.policy)
        cmd = mm_config.record_shell_with_cmd(save_dir, ["a", "command"])
        assert cmd == (mm_config.record_cmd(save_dir) + ["a", "command"])

    def test_record_cmd(self):
        save_dir = "/tmp/save_dir"
        mm_config = MahiMahiConfig(self.config)
        record_cmd = mm_config.record_cmd(save_dir)
        assert record_cmd[0] == "mm-webrecord"
        assert record_cmd[1] == save_dir

    def test_formatted_trace_file(self):
        mm_config = MahiMahiConfig(self.config, policy=self.policy, client_environment=self.client_environment)
        trace_lines = trace_for_kbps(self.client_environment.bandwidth)
        formatted = format_trace_lines(trace_lines)
        assert mm_config.formatted_trace_file == formatted
