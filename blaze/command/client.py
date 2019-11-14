""" Implements the command for querying a trained policy """
import json

import grpc

from blaze.config.client import get_client_environment_from_parameters
from blaze.config.environment import EnvironmentConfig
from blaze.logger import logger as log
from blaze.serve.client import Client

from . import command


@command.argument("--manifest", "-m", help="The location of the page manifest to query the model for", required=True)
@command.argument("--bandwidth", "-b", help="The bandwidth to query the model for (kbps)", type=int, required=True)
@command.argument("--latency", "-l", help="The latency to query the model for (ms)", type=int, required=True)
@command.argument(
    "--cpu_slowdown",
    "-s",
    help="The cpu slowdown of the device to query the model for",
    type=int,
    choices=[1, 2, 4],
    default=1,
)
@command.argument("--host", help="The host of the gRPC policy server to connect to", default="127.0.0.1")
@command.argument("--port", help="The port of the gRPC policy server to connect to", default=24450, type=int)
@command.command
def query(args):
    """
    Queries a trained model that is served on a gRPC server.
    """
    log.info("querying server...", host=args.host, port=args.port)

    channel = grpc.insecure_channel(f"{args.host}:{args.port}")
    client = Client(channel)

    manifest = EnvironmentConfig.load_file(args.manifest)
    client_env = get_client_environment_from_parameters(args.bandwidth, args.latency, args.cpu_slowdown)
    policy = client.get_policy(url=manifest.request_url, client_env=client_env, manifest=manifest)

    print(json.dumps(policy.as_dict, indent=4))


@command.argument("--location", help="The path to the saved model", required=True)
@command.argument(
    "--model",
    help="The RL technique used during training for the saved model",
    required=True,
    choices=["A3C", "APEX", "PPO"],
)
@command.argument("--manifest", "-m", help="The location of the page manifest to query the model for", required=True)
@command.argument("--bandwidth", "-b", help="The bandwidth to query the model for (kbps)", type=int, required=True)
@command.argument("--latency", "-l", help="The latency to query the model for (ms)", type=int, required=True)
@command.argument(
    "--cpu_slowdown",
    "-s",
    help="The cpu slowdown of the device to query the model for",
    type=int,
    choices=[1, 2, 4],
    default=1,
)
@command.argument("--verbose", "-v", help="Output more information in the JSON output", action="store_true")
@command.command
def evaluate(args):
    """
    Instantiate the given model and checkpoint and query it for the policy corresponding to the given
    client and network conditions.
    """
    log.info("evaluating model...", model=args.model, location=args.location, manifest=args.manifest)
    client_env = get_client_environment_from_parameters(args.bandwidth, args.latency, args.cpu_slowdown)
    manifest = EnvironmentConfig.load_file(args.manifest)

    if args.model == "A3C":
        from blaze.model import a3c as model
    if args.model == "APEX":
        from blaze.model import apex as model
    if args.model == "PPO":
        from blaze.model import ppo as model

    saved_model = model.get_model(args.location)
    instance = saved_model.instantiate(manifest, client_env)
    policy = instance.policy.as_dict

    if args.verbose:
        print(
            json.dumps(
                {
                    "manifest": args.manifest,
                    "location": args.location,
                    "client_env": client_env._asdict(),
                    "policy": policy,
                },
                indent=4,
            )
        )
    else:
        print(json.dumps(policy, indent=4))
