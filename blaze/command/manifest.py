""" Implements the commands for viewing and manipulating the training manifest """
import os

from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger as log
from blaze.preprocess.url import Url

from . import command


@command.argument("manifest_file", help="The file path to the saved manifest file from `blaze preprocess`")
@command.argument("--trainable", "-t", help="Only show trainable push groups", action="store_true", default=False)
@command.argument("--verbose", "-v", help="Show more information", action="store_true", default=False)
@command.command
def view_manifest(args):
    """ View the prepared manifest from `blaze preprocess` """
    log.info("loading manifest", manifest_file=args.manifest_file)
    env_config = EnvironmentConfig.load_file(args.manifest_file)

    print("[[ Request URL ]]\n{}\n".format(env_config.request_url))
    print("[[ Replay Dir ]]\n{}\n".format(env_config.replay_dir))
    print("[[ Trainable Groups ]]\n{}\n".format("\n".join(group.name for group in env_config.trainable_push_groups)))
    print("[[ {}Push Groups ]]".format("Trainable " if args.trainable else ""))

    for group in env_config.push_groups:
        if args.trainable and not group.trainable:
            continue
        print("  [{id}: {name} ({num} resources)]".format(id=group.id, name=group.name, num=len(group.resources)))
        for res in group.resources:
            url = Url.parse(res.url).resource
            if len(url) > 64:
                url = url[:61] + "..."
            print(
                "    {order:<3}  {url:<64}  {type:<6} {size:>8} B  cache: {cache}s  {crit}".format(
                    order=res.order,
                    url=url,
                    type=res.type.name,
                    size=res.size,
                    cache=res.cache_time,
                    crit="critical" if res.critical else "",
                )
            )
        print()

    print("[[ Execution Graph ]]")
    sim = Simulator(env_config)
    sim.print_execution_map()


@command.argument("manifest_file", help="The manifest file to update")
@command.argument("--replay_dir_path_prefix", help="Update the path prefix of the replay directory")
@command.argument("--replay_dir_folder_name", help="Update the folder name of replay directory")
@command.argument(
    "--save_as",
    help="Save the manifest in the specified location, making a copy of the original. "
    "This option does not modify the original manifest",
)
@command.argument("--train_domain_globs", nargs="*", help="The glob patterns of domain names to enable training for")
@command.command
def update_manifest(args):
    """
    Update the manifest file with the specified changes. This will replace the manifest file with the
    update version, unless --save_as is specified, in which case it will create a new manifest file in
    that location and leave the original one unmodified.
    """
    save_as = args.save_as or args.manifest_file
    log.info(
        "Updating manifest",
        manifest_file=args.manifest_file,
        replay_dir_path_prefix=args.replay_dir_path_prefix,
        replay_dir_folder_name=args.replay_dir_folder_name,
        save_as=save_as,
    )
    env_config = EnvironmentConfig.load_file(args.manifest_file)

    new_replay_dir = env_config.replay_dir
    if args.replay_dir_path_prefix:
        new_replay_dir = os.path.join(args.replay_dir_path_prefix, os.path.basename(new_replay_dir))

    if args.replay_dir_folder_name:
        new_replay_dir = os.path.join(os.path.dirname(new_replay_dir), args.replay_dir_folder_name)

    new_env_config = env_config._replace(replay_dir=new_replay_dir)
    new_env_config.save_file(save_as)
