""" This module defines the training configuration """
from typing import NamedTuple, Union


class TrainConfig(NamedTuple):
    """ TrainConfig is a configuration for training with ray """

    experiment_name: str
    num_workers: int
    resume: Union[bool, str] = "prompt"
