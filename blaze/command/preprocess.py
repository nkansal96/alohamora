""" Implements the commands for preprocessing webpages before training """
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.logger import logger as log

from blaze.preprocess.record import record_webpage, find_url_stable_set
from blaze.preprocess.resource import resource_list_to_push_groups

from . import command

@command.description('Prepare a website for training')
@command.argument('website', help='The URL of the website to prepare for training')
@command.argument('--depth', help='The recursive depth of URLs to process for the given page', default=0, type=int)
@command.argument('--output', help='The location to save the prepared manifest', required=True)
@command.argument('--record_dir', help='The directory to save the recorded webpage', required=True)
@command.command
def preprocess(args):
  """ Implement webpage preprocessing for training """
  log.info('preprocessing website', website=args.website, depth=args.depth)

  config = get_config()
  log.debug('using configuration', **config._asdict())

  log.info('saving recorded webpage...')
  record_webpage(args.website, args.record_dir, config)

  log.info('finding dependency stable set...')
  res_list = find_url_stable_set(args.website, config)

  log.info('found total dependencies', total=len(res_list))
  push_groups = resource_list_to_push_groups(res_list)

  log.info('generating configuration...')
  env_config = EnvironmentConfig(
    replay_dir=args.record_dir,
    request_url=args.website,
    push_groups=push_groups,
  )
  env_config.save_file(args.output)
  log.info('successfully prepared website for training', output=args.output)
