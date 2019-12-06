""" Implements the command for querying a trained policy """
import json
import cProfile
import pstats
import io
import grpc

from blaze.config.client import get_client_environment_from_parameters
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.analyzer import get_num_rewards
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.record import get_page_load_time_in_replay_server
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
@command.argument(
    "--reward_func", help="Reward function to use", default=1, choices=list(range(get_num_rewards())), type=int
)
@command.argument("--verbose", "-v", help="Output more information in the JSON output", action="store_true")
@command.argument(
    "--run_simulator", help="Run the outputted policy through the simulator (implies -v)", action="store_true"
)
@command.argument(
    "--run_replay_server", help="Run the outputted policy through the replay server (implies -v)", action="store_true"
)
@command.command
def evaluate(args):
    """
    Instantiate the given model and checkpoint and query it for the policy corresponding to the given
    client and network conditions. Also allows running the generated policy through the simulator and
    replay server to get the PLTs and compare them under different conditions.
    """
    log.info("evaluating model...", model=args.model, location=args.location, manifest=args.manifest)
    client_env = get_client_environment_from_parameters(args.bandwidth, args.latency, args.cpu_slowdown)
    manifest = EnvironmentConfig.load_file(args.manifest)
    config = get_config(manifest, client_env, args.reward_func)

    if args.model == "A3C":
        from blaze.model import a3c as model
    if args.model == "APEX":
        from blaze.model import apex as model
    if args.model == "PPO":
        from blaze.model import ppo as model

    import ray

    ray.init(num_cpus=2, log_to_driver=False)

    saved_model = model.get_model(args.location)
    instance = saved_model.instantiate(config)
    policy = instance.policy
    data = policy.as_dict

    if args.verbose or args.run_simulator or args.run_replay_server:
        data = {
            "manifest": args.manifest,
            "location": args.location,
            "client_env": client_env._asdict(),
            "policy": policy.as_dict,
        }

    if args.run_simulator:
        sim = Simulator(manifest)
        sim_plt = sim.simulate_load_time(client_env)
        push_plt = sim.simulate_load_time(client_env, policy)
        data["simulator"] = {"without_policy": sim_plt, "with_policy": push_plt}

    if args.run_replay_server:
        *_, plts = get_page_load_time_in_replay_server(config.env_config.request_url, client_env, config)
        *_, push_plts = get_page_load_time_in_replay_server(config.env_config.request_url, client_env, config, policy)
        data["replay_server"] = {"without_policy": plts, "with_policy": push_plts}

    print(json.dumps(data, indent=4))


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
@command.argument(
    "--reward_func", help="Reward function to use", default=1, choices=list(range(get_num_rewards())), type=int
)
@command.argument(
    "--output_file",
    help="File to save query timing profile info. First timing obtained right after launching Ray",
    required=True,
    type=str,
)
def get_inference_time(args):
    """
    Instantiate the given model and checkpoint and query it for the policy corresponding to the given
    client and network conditions. Returns time taken for querying for the policy.
    """
    log.info("evaluating model...", model=args.model, location=args.location, manifest=args.manifest)
    client_env = get_client_environment_from_parameters(args.bandwidth, args.latency, args.cpu_slowdown)
    manifest = EnvironmentConfig.load_file(args.manifest)
    config = get_config(manifest, client_env, args.reward_func)

    if args.model == "A3C":
        from blaze.model import a3c as model
    if args.model == "APEX":
        from blaze.model import apex as model
    if args.model == "PPO":
        from blaze.model import ppo as model

    import ray

    ray.init(num_cpus=2, log_to_driver=False)
    saved_model = model.get_model(args.location)
    instance = saved_model.instantiate(config)

    profiler_1 = cProfile.Profile()
    profiler_1.enable()
    _ = instance.policy
    profiler_1.disable()
    s = io.StringIO()
    p_stats_client = pstats.Stats(profiler_1, stream=s).sort_stats("tottime")
    p_stats_client.print_stats()
    profile_stats = s.getvalue().splitlines()
    with open(args.output_file, mode="w") as f:
        f.write(profile_stats[0].split(" ")[-2])
    ray.shutdown()
