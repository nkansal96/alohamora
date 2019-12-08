""" This module defines the main Config used in launching training tasks """

import os
import platform
from typing import NamedTuple, Optional, Set

from blaze.util.cmd import run
from .client import ClientEnvironment
from .environment import EnvironmentConfig


DEFAULT_HTTP2PUSH_IMAGE = "http2push"
DEFAULT_CHROME_BIN = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if platform.system() == "Darwin"
    else run(["which", "google-chrome"])
)


class Config(NamedTuple):
    """ Config defines the parameters required to run blaze """

    http2push_image: str
    chrome_bin: str

    # Training/Evaluation parameters
    env_config: Optional[EnvironmentConfig] = None
    client_env: Optional[ClientEnvironment] = None
    reward_func: Optional[int] = None
    use_aft: Optional[bool] = None
    cached_urls: Optional[Set[str]] = None

    def items(self):
        """ Return the dictionary items() method for this object """
        return self._asdict().items()  # pylint: disable=no-member

    def with_mutations(self, **kwargs) -> "Config":
        """ Returns a new Config object with the modified properties """
        return Config(
            http2push_image=kwargs.get("http2push_image", self.http2push_image),
            chrome_bin=kwargs.get("chrome_bin", self.chrome_bin),
            env_config=kwargs.get("env_config", self.env_config),
            client_env=kwargs.get("client_env", self.client_env),
            reward_func=kwargs.get("reward_func", self.reward_func),
            use_aft=kwargs.get("use_aft", self.use_aft),
            cached_urls=kwargs.get("cached_urls", self.cached_urls),
        )


def get_config(
    env_config: Optional[EnvironmentConfig] = None,
    client_env: Optional[ClientEnvironment] = None,
    reward_func: Optional[int] = None,
    use_aft: Optional[bool] = None,
) -> Config:
    """
    get_config returns the runtime configuration, taking values from environment variables
    when available to override the defaults
    """
    return Config(
        http2push_image=os.environ.get("HTTP2PUSH_IMAGE", DEFAULT_HTTP2PUSH_IMAGE),
        chrome_bin=os.environ.get("CHROME_BIN", DEFAULT_CHROME_BIN),
        env_config=env_config,
        client_env=client_env,
        reward_func=reward_func,
        use_aft=use_aft,
    )
