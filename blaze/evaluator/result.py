"""
This module defines classes and methods to represent and process the results
from Lighthouse
"""
import itertools


class Result:
    """ Result is the result from Lighthouse """

    def __init__(self, **res):
        self.speed_index = res.get("speedIndex", 0)

    def __repr__(self):
        return "Result<{}>".format(" ".join(itertools.starmap("{}={}".format, vars(self).items())))
