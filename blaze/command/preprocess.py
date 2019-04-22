""" Implements the commands for preprocessing webpages before training """
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.logger import logger as log

from blaze.preprocess.record import record_webpage, find_url_stable_set
from blaze.preprocess.resource import resource_list_to_push_groups
from blaze.preprocess.url import Url

from . import command

@command.argument('website', help='The URL of the website to prepare for training')
@command.argument('--depth', help='The recursive depth of URLs to process for the given page', default=0, type=int)
@command.argument('--output', help='The location to save the prepared manifest', required=True)
@command.argument('--train_domain_suffix', help='The suffix of domain names to enable training for. By default this '
                                                'will be the domain of the given URL')
@command.argument('--record_dir', help='The directory to save the recorded webpage', required=True)
@command.command
def preprocess(args):
  """
  Preprocesses a website for training. Automatically discovers linked pages up to a certain depth
  and finds the stable set of page dependencies. The page load is recorded and stored and a
  training manifest is outputted.
  """
  domain = args.train_domain_suffix or Url.parse(args.website).domain
  log.info('preprocessing website', website=args.website, depth=args.depth, train_domain="*.{}".format(domain))

  config = get_config()
  log.debug('using configuration', **config._asdict())

  log.info('saving recorded webpage...')
  record_webpage(args.website, args.record_dir, config)

  log.info('finding dependency stable set...')
  res_list = find_url_stable_set(args.website, config)

  log.info('found total dependencies', total=len(res_list))
  push_groups = resource_list_to_push_groups(res_list, train_domain_suffix=domain)

  log.info('generating configuration...')
  env_config = EnvironmentConfig(
    replay_dir=args.record_dir,
    request_url=args.website,
    push_groups=push_groups,
  )
  env_config.save_file(args.output)
  log.info('successfully prepared website for training', output=args.output)


@command.argument('manifest_file', help='The file path to the saved manifest file from `blaze preprocess`')
@command.argument('--verbose', '-v', help='Show more information', action='store_true', default=False)
@command.command
def view_manifest(args):
  """ View the prepared manifest from `blaze preprocess` """
  log.info('loading manifest', manifest_file=args.manifest_file)
  env_config = EnvironmentConfig.load_file(args.manifest_file)

  print('[[ Request URL ]]\n{}\n'.format(env_config.request_url))
  print('[[ Replay Dir ]]\n{}\n'.format(env_config.replay_dir))
  print('[[ Trainable Groups ]]\n{}\n'.format('\n'.join(group.name for group in env_config.push_groups
                                                        if group.trainable)))
  print('[[ Push Groups]]')

  for group in env_config.push_groups:
    print('  [{id}: {name} ({num} resources)]'.format(
      id=group.id,
      name=group.name,
      num=len(group.resources),
    ))
    for res in group.resources:
      url = Url.parse(res.url).resource
      if len(url) > 64:
        url = url[:61] + '...'
      print('    {order:<3}  {url:<64}  {type:<6}  {size} B'.format(
        order=res.order,
        url=url,
        type=res.type.name,
        size=res.size,
      ))
    print()
