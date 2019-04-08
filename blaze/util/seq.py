""" This module contains utility functions to operate on sequences """
from typing import Any, Callable, Hashable, Iterable, List, TypeVar

T = TypeVar('T')
def ordered_uniq(seq: Iterable[T], key: Callable[[T], Hashable] = lambda x: x) -> List[T]:
  """
  Returns the list of unique elements from the given sequence using the
  given key function. This method retains the order of the original list,
  taking the first element that is unique
  """
  seen = set()
  res = []
  for item in seq:
    item_key = key(item)
    if item_key not in seen:
      res.append(item)
      seen.add(item_key)
  return res
