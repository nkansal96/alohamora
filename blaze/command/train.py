""" Implements the commands for training """
import multiprocessing
import sys

from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.config.train import TrainConfig
from blaze.logger import logger as log

from . import command

@command.argument('name', help='The name of the experiment')
@command.argument('--dir', help='The location to save the model', required=True)
@command.argument('--model', help='The RL technique to use while training', default='APEX', choices=['APEX', 'PPO'])
@command.argument('--cpus', help='Number of CPUs to use for training', default=multiprocessing.cpu_count(), type=int)
@command.argument('--timesteps', help='Maximum number of timesteps to train for', default=10000000, type=int)
@command.argument('--manifest_file', help='A description of the website that should be trained. This should be the '
                                          'generated by `blaze preprocess`', required=True)
@command.argument('--resume', help='Resume training from last checkpoint', default=False, action='store_true')
@command.argument('--no-resume', help='Start a new training session even if a previous checkpoint is available',
                  default=False, action='store_true')
@command.command
def train(args):
  """
  Trains a model to generate push policies for the given website. This command takes as input the
  manifest file generated by `blaze preprocess` and outputs a model that can be served.
  """
  # check for ambiguous options
  if args.resume and args.no_resume:
    log.error('invalid options: cannot specify both --resume and --no-resume',
              resume=args.resume, no_resume=args.no_resume)
    sys.exit(1)

  log.info('starting train', name=args.name, model=args.model)
  # import specified model
  if args.model == 'APEX':
    from blaze.model import apex as model
  if args.model == 'PPO':
    from blaze.model import ppo as model

  # compute resume flag and initialize training
  resume = False if args.no_resume else True if args.resume else "prompt"
  train_config = TrainConfig(
    experiment_name=args.name,
    model_dir=args.dir,
    num_cpus=args.cpus,
    max_timesteps=args.timesteps,
    resume=resume
  )
  env_config = EnvironmentConfig.load_file(args.manifest_file)
  config = get_config(env_config)
  model.train(train_config, config)
