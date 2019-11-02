""" Implements the command for querying a trained policy """
import json

import grpc

from blaze.config.client import NetworkType, DeviceSpeed
from blaze.config.environment import EnvironmentConfig
from blaze.logger import logger as log
from blaze.serve.client import Client

from . import command


@command.argument("--manifest", "-m", help="The location of the page manifest to query the model for", required=True)
@command.argument(
    "--network_type",
    "-n",
    help="The network type to query the model for (see blaze.config.client.NetworkType for valid choices)",
    type=int,
    choices=list(range(len(NetworkType))),
    required=True,
)
@command.argument(
    "--device_speed",
    "-d",
    help="The device speed to query the model for (see blaze.config.client.DeviceSpeed for valid choices)",
    type=int,
    choices=list(range(len(DeviceSpeed))),
    required=True,
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
    policy = client.get_policy(
        url=manifest.request_url,
        network_type=NetworkType(args.network_type),
        device_speed=DeviceSpeed(args.device_speed),
        resources=[res for group in manifest.push_groups for res in group.resources],
        train_domain_globs=[group.name for group in manifest.push_groups if group.trainable],
    )

    print(json.dumps(policy.as_dict, indent=4))
