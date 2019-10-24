import random

from typing import List, Tuple

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.config.config import Config, get_config as _get_config
from blaze.config.environment import PushGroup, Resource, ResourceType, EnvironmentConfig
from blaze.config.serve import ServeConfig
from blaze.config.train import TrainConfig
from blaze.mahimahi.mahimahi import MahiMahiConfig


def get_push_groups() -> List[PushGroup]:
    return [
        PushGroup(
            id=0,
            name="example.com",
            trainable=True,
            resources=[
                Resource(
                    url="http://example.com/",
                    size=1024,
                    order=0,
                    group_id=0,
                    source_id=0,
                    initiator=0,
                    type=ResourceType.HTML,
                ),
                Resource(
                    url="http://example.com/A",
                    size=1024,
                    order=1,
                    group_id=0,
                    source_id=1,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
                Resource(
                    url="http://example.com/B",
                    size=1024,
                    order=5,
                    group_id=0,
                    source_id=2,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
                Resource(
                    url="http://example.com/C",
                    size=1024,
                    order=8,
                    group_id=0,
                    source_id=3,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
                Resource(
                    url="http://example.com/F",
                    size=1024,
                    order=12,
                    group_id=0,
                    source_id=4,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
            ],
        ),
        PushGroup(
            id=1,
            name="img.example.com",
            trainable=True,
            resources=[
                Resource(
                    url="http://img.example.com/D",
                    size=1024,
                    order=9,
                    group_id=1,
                    source_id=0,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
                Resource(
                    url="http://img.example.com/E",
                    size=1024,
                    order=11,
                    group_id=1,
                    source_id=1,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
                Resource(
                    url="http://img.example.com/G",
                    size=1024,
                    order=13,
                    group_id=1,
                    source_id=2,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
            ],
        ),
        PushGroup(
            id=2,
            name="serve.ads.googleads.com",
            trainable=False,
            resources=[
                Resource(
                    url="http://serve.ads.googleads.com/script.1.js",
                    size=1024,
                    order=4,
                    group_id=2,
                    source_id=0,
                    initiator=0,
                    type=ResourceType.SCRIPT,
                ),
                Resource(
                    url="http://serve.ads.googleads.com/script.2.js",
                    size=1024,
                    order=7,
                    group_id=2,
                    source_id=1,
                    initiator=4,
                    type=ResourceType.SCRIPT,
                ),
                Resource(
                    url="http://serve.ads.googleads.com/script.3.js",
                    size=1024,
                    order=10,
                    group_id=2,
                    source_id=2,
                    initiator=7,
                    type=ResourceType.SCRIPT,
                ),
            ],
        ),
        PushGroup(
            id=3,
            name="static.example.com",
            trainable=True,
            resources=[
                Resource(
                    url="http://static.example.com/script.js",
                    size=1024,
                    order=2,
                    group_id=3,
                    source_id=0,
                    initiator=4,
                    type=ResourceType.SCRIPT,
                ),
                Resource(
                    url="http://static.example.com/font.woff",
                    size=1024,
                    order=3,
                    group_id=3,
                    source_id=1,
                    initiator=10,
                    type=ResourceType.FONT,
                ),
                Resource(
                    url="http://static.example.com/image.jpg",
                    size=1024,
                    order=6,
                    group_id=3,
                    source_id=2,
                    initiator=0,
                    type=ResourceType.IMAGE,
                ),
            ],
        ),
    ]


def convert_push_groups_to_push_pairs(push_groups: List[PushGroup]) -> List[Tuple[Resource, Resource]]:
    return [
        (group.resources[s], group.resources[p])
        for group in push_groups
        for s in range(len(group.resources))
        for p in range(s + 1, len(group.resources))
    ]


def get_env_config() -> EnvironmentConfig:
    return EnvironmentConfig(
        replay_dir="/tmp/replay_dir",
        request_url="http://example.com/",
        push_groups=get_push_groups(),
        har_resources=sorted([res for group in get_push_groups() for res in group.resources], key=lambda r: r.order),
    )


def get_train_config() -> TrainConfig:
    return TrainConfig(experiment_name="test", model_dir="/tmp/test", num_cpus=4, max_timesteps=10)


def get_serve_config() -> ServeConfig:
    return ServeConfig(host="0.0.0.0", port=41568 + random.randint(0, 1000), max_workers=1)


def get_config(eval_results_dir=None) -> Config:
    return _get_config(env_config=get_env_config(), eval_results_dir=eval_results_dir)


def get_mahimahi_config() -> MahiMahiConfig:
    return MahiMahiConfig(
        config=get_config(),
        push_policy=Policy(ActionSpace(get_push_groups())),
        client_environment=get_random_client_environment(),
    )
