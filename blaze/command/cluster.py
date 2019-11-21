""" Implements the commands for clustering page trees """

import glob
import json

from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.cluster import AffinityCluster
from blaze.evaluator.cluster.distance import create_apted_distance_function
from blaze.logger import logger

from . import command


@command.argument("folder", help="The directory containing the manifests to cluster")
@command.argument("--apted_port", help="Port of APTED server", default=24451, type=int)
@command.command
def cluster(args):
    """ Cluster the given folder of pages """
    log = logger.with_namespace("cluster")
    log.info("clustering pages", folder=args.folder)

    def read_file(fpath):
        log.debug("reading file...", file=fpath)
        return EnvironmentConfig.load_file(fpath)

    files = list(map(read_file, glob.iglob(f"{args.folder}/*")))
    distance_func = create_apted_distance_function(args.apted_port)
    c = AffinityCluster(distance_func)
    mapping = c.cluster(files)
    print(json.dumps({f.request_url: int(i) for f, i in zip(files, mapping)}, indent=4))
