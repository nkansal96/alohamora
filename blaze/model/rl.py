import collections
import functools
import glob
import json
import os

import ray
import ray.rllib.agents.ppo as ppo
import ray.rllib.agents.dqn as dqn
import ray.tune as tune

import environment
import callbacks

WEBSITE = 'www.cnn.com'
NUM_URLS = 47 if WEBSITE == 'www.cs.ucla.edu' else 130

ENV_CONFIG = {
  **json.load(open('training/websites/' + WEBSITE + '/spec.json')),
  "throttling_settings": json.load(open('training/throttling/tmobile_lte.json')),
}

def train(env_config):
  ray.init(num_cpus=4)
  name = "demo-" + WEBSITE
  tune.run_experiments({
    name : {
      "run": "APEX",
      "env": environment.Browser,
      "stop": {
        "timesteps_total": 1000000,
      },
      "checkpoint_at_end": True,
      "checkpoint_freq": 1,
      "max_failures": 20,
      "config": {
        "sample_batch_size": 50,
        "train_batch_size": 512,
        "timesteps_per_iteration": NUM_URLS,
        "target_network_update_freq": NUM_URLS * 5,
        "batch_mode": "complete_episodes",
        "collect_metrics_timeout": 1200,
        "num_workers": 2,
        "num_gpus": 0,
        "env_config": env_config,
        # "callbacks": {
        #   "on_episode_start": tune.function(callbacks.on_episode_start),
        #   "on_episode_step": tune.function(callbacks.on_episode_step),
        #   "on_episode_end": tune.function(callbacks.on_episode_end),
        # }
      },
    },
  }, resume='prompt')

def get_policy(path, env_config):
  ray.init()
  agent = dqn.ApexAgent(env=environment.Browser, config={
    **dqn.apex.APEX_DEFAULT_CONFIG.copy(),
    "sample_batch_size": 50,
    "train_batch_size": 512,
    "timesteps_per_iteration": 47,
    "target_network_update_freq": 200,
    "batch_mode": "complete_episodes",
    "collect_metrics_timeout": 600,
    "num_workers": 2,
    "num_gpus": 0,
    "env_config": env_config,
  })
  agent.restore(path)
  env = {"push": collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))}
  for i in range(47):
    print(agent.compute_action(env))
  print(env)

if __name__ == '__main__':
  #home = '/home/ameesh'
  #results_dir = 'ray_results'
  #experiment_dir = 'demo-' + WEBSITE
  #search_dir = os.path.join(home, results_dir, experiment_dir)
  #search_glob = "{}/**/checkpoint-*".format(search_dir)
  #checkpoint_file = sorted(glob.glob(search_glob, recursive=True))[-2]
  #print(checkpoint_file)
  #get_policy(checkpoint_file, ENV_CONFIG)
  train(ENV_CONFIG)
  # initialize_web_root(WEB_ROOT, ENV_CONFIG)
