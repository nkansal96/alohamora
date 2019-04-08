""" This module defines methods to assist in manipulating URLs """
from typing import NamedTuple

class Url(NamedTuple):
  """ Url is a decomposition of the main components of a URL """
  scheme: str
  domain: str
  resource: str

  @property
  def url(self):
    """ Return the original URL from the decomposed components """
    # Disable no-member because ._asdict() actually does exist as a member function
    # inherited from NamedTuple, but for some reason pylint does not recognize it.
    return '{scheme}://{domain}{resource}'.format(**self._asdict()) # pylint: disable=no-member

  @staticmethod
  def parse(url: str):
    """ Parse a valid URL string into a Url """
    scheme = url.split('://')[0]
    domain = url.split('://')[1].split('/')[0]
    if len(url.split('://')[1].split('/')) == 1:
      resource = '/'
    else:
      resource = '/' + url.split('://')[1].split('/', maxsplit=1)[1]
    return Url(scheme, domain, resource)
