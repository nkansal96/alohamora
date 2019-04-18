import copy
import random
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

  def test_har_entries_to_resources_ignores_non_http_and_non_complete(self):
    entries = []
    entry_urls = set()
    invalid_entries = set()
    for entry in self.har.log.entries:
      if random.random() < 0.1:
        entry_copy = copy.deepcopy(entry)
        if random.random() < 0.5:
          entry_copy.request.url = "data:image/png;base64,asdflhqp49tqo3hifehqp" + str(random.random())[2:] + "=="
        else:
          entry_copy.response.status = 0
        entries.append(entry_copy)
        invalid_entries.add(entry_copy.request.url)
        print("invalid: {}".format(entry_copy.request.url))
      else:
        entries.append(entry)
        entry_urls.add(entry.request.url)

    invalid_entries = invalid_entries - set(entry_urls)
    resources = har_entries_to_resources(entries)

    assert len(resources) < len(entries) - len(invalid_entries)
    assert not any(res.url in invalid_entries for res in resources)
    assert all(res.url in entry_urls for res in resources)

