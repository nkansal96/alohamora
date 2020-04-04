""" Implements the commands for converting a push policy to an nginx configuration """
import json
from typing import List

from blaze.action import Policy
from blaze.config.environment import EnvironmentConfig, PushGroup
from blaze.mahimahi.server.nginx_config_without_lua import Config
from blaze.logger import logger as log

from . import command

@command.argument("--policy", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output", help="The filepath  to save the prepared nginx config", required=True)
@command.argument("--hostname", help="The hostname of the website for which this push policy is applicable. Do not include the protocol. Eg. www.walgreens.com", required=True)
@command.command
def convert(args):
    """
    Convert a push policy to an nginx proxy configuration file. 
    """
    log.debug("reading policy", push_policy=args.policy)
    with open(args.policy, "r") as policy_file:
        policy_dict = json.load(policy_file)
    policy = Policy.from_dict(policy_dict)
    
    config = Config()
    server_block = config.http_block.add_server(server_name=args.hostname,server_addr="127.0.0.1")

    for ptype, policy_obj in policy_dict.items():
        if ptype == "push" or ptype == "preload":
            for (source, deps) in policy_obj.items():
                location_block = server_block.add_location_block(uri=source)
                log.debug("source is ", url=source)
                for obj in deps:
                    if ptype == "push":
                        location_block.add_push(uri=obj["url"])
                        log.debug("child is ", url=obj["url"])
                    elif ptype == "preload":
                        location_block.add_preload(uri=obj["url"], as_type=obj["type"])
                        log.debug("child is ", url=obj["url"])
    log.debug("final config is ", nginx_config=config)
