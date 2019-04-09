import os
from unittest import mock

from blaze.config import config
from tests.mocks.config import get_env_config

class TestConfig():
  def test_create(self):
    conf = config.Config(
      mahimahi_cert_dir='',
      chrome_har_capturer_bin='',
      pwmetrics_bin='',
      nghttpx_bin='',
      chrome_bin='',
    )
    assert isinstance(conf, config.Config)
    assert conf.train_config is None

  def test_items(self):
    conf = config.get_config()
    items = conf.items()
    assert all(len(v) == 2 for v in items)
    assert len(items) == 6

class TestGetConfig():
  def test_get_default_config(self):
    conf = config.get_config()
    assert isinstance(conf, config.Config)
    assert conf.mahimahi_cert_dir == config.DEFAULT_MAHIMAHI_CERT_DIR
    assert conf.chrome_har_capturer_bin == config.DEFAULT_CHROME_HAR_CAPTURER_BIN
    assert conf.pwmetrics_bin == config.DEFAULT_PWMETRICS_BIN
    assert conf.nghttpx_bin == config.DEFAULT_NGHTTPX_BIN
    assert conf.chrome_bin == config.DEFAULT_CHROME_BIN
    assert conf.train_config is None

  def test_get_config_with_env_config(self):
    conf = config.get_config(get_env_config())
    assert conf.train_config == get_env_config()

  @mock.patch.dict(os.environ, {'CHROME_BIN': 'test_chrome', 'MAHIMAHI_CERT_DIR': 'test_mm_dir'})
  def test_get_config_with_override(self):
    conf = config.get_config()
    assert isinstance(conf, config.Config)
    assert conf.mahimahi_cert_dir == 'test_mm_dir'
    assert conf.chrome_har_capturer_bin == config.DEFAULT_CHROME_HAR_CAPTURER_BIN
    assert conf.pwmetrics_bin == config.DEFAULT_PWMETRICS_BIN
    assert conf.nghttpx_bin == config.DEFAULT_NGHTTPX_BIN
    assert conf.chrome_bin == 'test_chrome'
    assert conf.train_config is None
