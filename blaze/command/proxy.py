""" Implements the commands for converting a push policy to an nginx configuration """
from pathlib import Path
import json
import sys
from typing import List

from blaze.action import Policy
from blaze.config.environment import EnvironmentConfig, PushGroup
from blaze.mahimahi.server.nginx_config_without_lua import Config
from blaze.logger import logger as log

from . import command

@command.argument("--policy", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output", help="The filepath  to save the prepared nginx config", required=True)
@command.argument("--hostname", help="The hostname of the website for which this push policy is applicable. Do not include the protocol. Eg. www.walgreens.com", required=True)
@command.command
def convert(args):
	"""
	Convert a push policy to an nginx proxy configuration file. 
	"""
	log.debug("reading policy", push_policy=args.policy)
	with open(args.policy, "r") as policy_file:
		policy_dict = json.load(policy_file)
	policy = Policy.from_dict(policy_dict)
	
	config = Config()
	server_block = config.http_block.add_server(server_name=args.hostname,server_addr="127.0.0.1")

	for ptype, policy_obj in policy_dict.items():
		if ptype == "push" or ptype == "preload":
			for (source, deps) in policy_obj.items():
				location_block = server_block.add_location_block(uri=source)
				log.debug("source is ", url=source)
				for obj in deps:
					if ptype == "push":
						location_block.add_push(uri=obj["url"])
						log.debug("child is ", url=obj["url"])
					elif ptype == "preload":
						location_block.add_preload(uri=obj["url"], as_type=obj["type"])
						log.debug("child is ", url=obj["url"])
	log.debug("final config is ", nginx_config=config)
	with open(args.output, "w") as f:
		f.write(str(config))


@command.argument("--input_folder", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output_folder", help="The filepath  to save the prepared nginx config", required=True)
@command.command
def convert_folder(args):
	"""
	Takes in a folder that contains a number of push policy files. 
	Each file should be json formatted with a url, push and preload fields. 
	The output folder should exist prior to calling the command.
	A set of nginx configuration files will be created: one for each domain. 
	The command skips setting push/preload values for overlapping uris. 
	This is because multiple sites may have different rules for the same uri. 
	"""
	folder = args.input_folder
	result_files = []
	file_paths = list(Path(folder).rglob("*.[jJ][sS][oO][nN]"))
	for posix_file_path in file_paths:
		f = str(posix_file_path)
		try:
			log.debug("reading policy", push_policy=f)
			with open(f, "r") as policy_file:
				policy_dict = json.load(policy_file)
			policy = Policy.from_dict(policy_dict)
			
			config = Config()
			server_block = config.http_block.add_server(server_name="domain.com",server_addr="127.0.0.1")
			for ptype, policy_obj in policy_dict.items():
				if ptype == "push" or ptype == "preload":
					for (source, deps) in policy_obj.items():
						location_block = server_block.add_location_block(uri=source)
						for obj in deps:
							if ptype == "push":
								location_block.add_push(uri=obj["url"])
							elif ptype == "preload":
								location_block.add_preload(uri=obj["url"], as_type=obj["type"])
			log.debug("final config is ", nginx_config=config)

		except json.JSONDecodeError as e:
			print("failed to decode json for " + f + ", err: " + str(e), file=sys.stderr)
