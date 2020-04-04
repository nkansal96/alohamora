""" Implements the commands for converting a push policy to an nginx configuration """
from typing import List

from blaze.action import Policy
from blaze.config.environment import EnvironmentConfig, PushGroup
from blaze.logger import logger as log

from . import command

@command.argument("--policy", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output", help="The filepath  to save the prepared nginx config", required=True)
@command.command
def convert(args):
    """
    Convert a push policy to an nginx proxy configuration file. 
    """
    log.debug("reading policy", push_policy=args.policy)
    with open(args.policy, "r") as policy_file:
        policy_dict = json.load(policy_file)
    policy = Policy.from_dict(policy_dict)
    for item in policy.push():
        log.debug("loaded item is ", item=item)
