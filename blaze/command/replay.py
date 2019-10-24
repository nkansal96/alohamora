""" Implements the commands for viewing and manipulating the training manifest """
import json
import time

from blaze.action import Policy
from blaze.logger import logger as log
from blaze.mahimahi.server import start_server

from . import command


@command.argument("replay_dir", help="The directory containing the save files captured by mahimahi")
@command.argument("--push_policy", help="The file path to a JSON-formatted push policy to serve")
@command.argument("--preload_policy", help="The file path to a JSON-formatted preload policy to serve")
@command.argument("--cert_path", help="Location of the server certificate")
@command.argument("--key_path", help="Location of the server key")
@command.command
def replay(args):
    """
    Starts a replay environment for the given replay directory, including setting up interfaces, running
    a DNS server, and configuring and running an nginx server to serve the requests
    """
    push_policy = None
    preload_policy = None
    if args.push_policy:
        log.debug("reading push policy", push_policy=args.push_policy)
        with open(args.push_policy, "r") as policy_file:
            policy_dict = json.load(policy_file)
        push_policy = Policy.from_dict(policy_dict)
    if args.preload_policy:
        log.debug("reading preload policy", preload_policy=args.preload_policy)
        with open(args.preload_policy, "r") as policy_file:
            policy_dict = json.load(policy_file)
        preload_policy = Policy.from_dict(policy_dict)

    with start_server(args.replay_dir, args.cert_path, args.key_path, push_policy, preload_policy):
        while True:
            time.sleep(86400)
