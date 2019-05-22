from blaze.chrome.config import get_chrome_command, get_chrome_flags
from tests.mocks.config import get_config


def test_get_chrome_flags():
    user_data_dir = "/tmp/chrome_data"
    required_flags = [
        "allow-insecure-localhost",
        "headless",
        "ignore-certificate-errors",
        "user-data-dir={}".format(user_data_dir),
    ]
    flags = " ".join(get_chrome_flags(user_data_dir))
    assert all(flag in flags for flag in required_flags)


def test_get_chrome_command():
    user_data_dir = "/tmp/chrome_data"
    url = "http://example.com"
    flags = get_chrome_flags(user_data_dir)
    config = get_config()
    chrome_cmd = get_chrome_command(url, flags, config)
    assert config.chrome_bin == chrome_cmd[0]
    assert flags == chrome_cmd[1:-1]
    assert url == chrome_cmd[-1]
