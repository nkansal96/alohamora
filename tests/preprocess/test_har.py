from types import SimpleNamespace
from unittest import mock

from blaze.chrome.devtools import capture_har
from blaze.chrome.har import har_from_json
from blaze.config.environment import ResourceType
from blaze.preprocess.har import get_har_entry_type, har_entries_to_resources
from blaze.util.seq import ordered_uniq

from tests.mocks.config import get_config
from tests.mocks.har import get_har_json

class TestGetHarEntryType():
  def test_get_har_entry_type(self):
    test_cases = [
      ('application/javascript', ResourceType.SCRIPT),
      ('application/json', ResourceType.OTHER),
      ('audio/aac', ResourceType.OTHER),
      ('image/jpeg', ResourceType.IMAGE),
      ('image/gif', ResourceType.IMAGE),
      ('text/html', ResourceType.HTML),
      ('text/css', ResourceType.CSS),
      ('text/xml', ResourceType.OTHER),
      ('font/woff2', ResourceType.FONT),
      ('font/oft', ResourceType.FONT),
    ]
    for (mime_type, resource_type) in test_cases:
      har_entry = SimpleNamespace(response=SimpleNamespace(content=SimpleNamespace(mimeType=mime_type)))
      assert get_har_entry_type(har_entry) == resource_type

class TestHarEntriesToResources():
  def setup(self):
    self.config = get_config()
    self.har = har_from_json(get_har_json())

  def test_har_entries_to_resources(self):
    resources = har_entries_to_resources(self.har.log.entries)
    assert resources
    sorted_har_entries = sorted(self.har.log.entries, key=lambda e: e.startedDateTime)
    sorted_har_entries = ordered_uniq(sorted_har_entries, key=lambda e: e.request.url)
    for har_entry, resource in zip(sorted_har_entries, resources):
      assert har_entry.request.url == resource.url
