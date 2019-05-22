""" This module defines methods to configure an instance of Chrome """
from typing import List, Optional
from blaze.config import Config


def get_chrome_flags(user_data_dir: str, extra_flags: Optional[List[str]] = None) -> List[str]:
    """
    Returns the default flags to run chrome with. Allows extra flags to be incorporated.
    Passing a temporary user_data_dir ensures that Chrome page loads are not affected by
    caches and other settings.
    """
    # https://peter.sh/experiments/chromium-command-line-switches/
    return [
        "--allow-insecure-localhost",
        "--disable-background-networking",
        "--disable-default-apps",
        # '--disable-gpu',
        "--disable-logging",
        # '--disable-renderer-backgrounding',
        # '--disable-threaded-animation',
        # '--disable-threaded-compositing',
        # '--disable-threaded-scrolling',
        # '--disable-threaded-animation',
        "--headless",
        "--ignore-certificate-errors",
        "--no-check-certificate",
        "--no-default-browser-check",
        "--no-first-run",
        "--user-data-dir={}".format(user_data_dir),
        *(extra_flags if extra_flags else []),
    ]


def get_chrome_command(url: str, flags: List[str], config: Config) -> List[str]:
    """ Given a url, flags, and config, return a command to run chrome """
    return [config.chrome_bin, *flags, url]
