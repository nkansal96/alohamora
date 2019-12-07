""" Describes types used to configure the training environment """

import enum
import pickle
from typing import List, NamedTuple


class ResourceType(enum.IntEnum):
    """ ResourceType defines the type of a particular resource """

    NONE = 0
    HTML = 1
    SCRIPT = 2
    CSS = 3
    IMAGE = 4
    FONT = 5
    OTHER = 6


class Resource(NamedTuple):
    """ Resource defines a particular resource in a page """

    url: str
    size: int
    type: ResourceType

    order: int = 0
    group_id: int = 0
    source_id: int = 0
    initiator: int = 0

    cache_time: int = 0
    critical: bool = False

    execution_ms: float = 0
    fetch_delay_ms: float = 0
    time_to_first_byte_ms: float = 0

    def __eq__(self, other):
        return self.url == other.url

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.url)


class PushGroup(NamedTuple):
    """ PushGroup collects a group of resources for the same domain """

    id: int
    name: str
    resources: List[Resource]
    trainable: bool = True


class EnvironmentConfig(NamedTuple):
    """ EnvironmentConfig is the main configuration used in setting up the training environment """

    replay_dir: str
    request_url: str
    push_groups: List[PushGroup] = []
    har_resources: List[Resource] = []

    @property
    def trainable_push_groups(self):
        """ Returns the subset of push_groups that is trainable """
        return [group for group in self.push_groups if group.trainable]

    def serialize(self) -> bytes:
        """ Returns a pickled representation of the training manifest """
        return pickle.dumps(self)

    def save_file(self, file_name: str):
        """ Serialize the EnvironmentConfig to the given file path """
        pickle.dump(self, open(file_name, "wb"))

    @staticmethod
    def load_file(file_name: str) -> "EnvironmentConfig":
        """ Load an EnvironmentConfig from the given file path """
        return pickle.load(open(file_name, "rb"))

    @staticmethod
    def deserialize(data: bytes) -> "EnvironmentConfig":
        """ Loads pickled byte data into an EnvironmentConfig """
        return pickle.loads(data)
