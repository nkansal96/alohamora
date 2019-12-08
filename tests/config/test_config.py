import os
from unittest import mock

from blaze.config import config
from tests.mocks.config import get_env_config
from tests.mocks.config import get_random_client_environment


class TestConfig:
    def test_create(self):
        conf = config.Config(http2push_image="", chrome_bin="")
        assert isinstance(conf, config.Config)
        assert conf.env_config is None
        assert conf.client_env is None
        assert conf.reward_func is None
        assert conf.use_aft is None

    def test_items(self):
        conf = config.get_config()
        items = conf.items()
        assert all(len(v) == 2 for v in items)
        assert len(items) == 7

    def test_with_mutations(self):
        conf = config.Config(http2push_image="", chrome_bin="")
        conf2 = conf.with_mutations()
        assert conf == conf2
        conf2 = conf.with_mutations(reward_func=1)
        assert conf.reward_func is None
        assert conf2.reward_func == 1


class TestGetConfig:
    def test_get_default_config(self):
        conf = config.get_config()
        assert isinstance(conf, config.Config)
        assert conf.http2push_image == config.DEFAULT_HTTP2PUSH_IMAGE
        assert conf.chrome_bin == config.DEFAULT_CHROME_BIN
        assert conf.env_config is None
        assert conf.client_env is None
        assert conf.reward_func is None

    def test_get_config_with_env_config(self):
        conf = config.get_config(get_env_config())
        assert conf.env_config == get_env_config()

    def test_get_config_with_other_properties(self):
        client_env = get_random_client_environment()
        conf = config.get_config(get_env_config(), client_env, 0)
        assert conf.env_config == get_env_config()
        assert conf.client_env == client_env
        assert conf.reward_func == 0

    @mock.patch.dict(os.environ, {"CHROME_BIN": "test_chrome", "HTTP2PUSH_IMAGE": "test_image"})
    def test_get_config_with_override(self):
        conf = config.get_config()
        assert isinstance(conf, config.Config)
        assert conf.http2push_image == "test_image"
        assert conf.chrome_bin == "test_chrome"
        assert conf.env_config is None
