import copy
import random
from types import SimpleNamespace
from unittest import mock

from blaze.chrome.devtools import capture_har
from blaze.chrome.har import har_from_json, Har, HarLog, HarEntry, Request, Response
from blaze.config.environment import ResourceType
from blaze.preprocess.har import get_har_entry_type, har_entries_to_resources
from blaze.util.seq import ordered_uniq

from tests.mocks.config import get_config
from tests.mocks.har import get_har_json


class TestGetHarEntryType:
    def test_get_har_entry_type(self):
        test_cases = [
            ("application/javascript", ResourceType.SCRIPT),
            ("application/json", ResourceType.OTHER),
            ("audio/aac", ResourceType.OTHER),
            ("image/jpeg", ResourceType.IMAGE),
            ("image/gif", ResourceType.IMAGE),
            ("text/html", ResourceType.HTML),
            ("text/css", ResourceType.CSS),
            ("text/xml", ResourceType.OTHER),
            ("font/woff2", ResourceType.FONT),
            ("font/oft", ResourceType.FONT),
        ]
        for (mime_type, resource_type) in test_cases:
            har_entry = HarEntry(
                started_date_time="",
                request=Request(url="", method=""),
                response=Response(status=200, body_size=0, headers_size=0, mime_type=mime_type),
            )
            assert get_har_entry_type(har_entry) == resource_type


class TestHarEntriesToResources:
    def setup(self):
        self.config = get_config()
        self.har = har_from_json(get_har_json())

    def test_har_entries_to_resources(self):
        resources = har_entries_to_resources(self.har)
        assert resources
        sorted_har_entries = sorted(self.har.log.entries, key=lambda e: e.started_date_time)
        sorted_har_entries = ordered_uniq(sorted_har_entries, key=lambda e: e.request.url)
        sorted_har_entries = [entry for entry in sorted_har_entries if entry.request.url.startswith("http")]
        sorted_har_entries = [entry for entry in sorted_har_entries if entry.response.status != 0]
        for har_entry, resource in zip(sorted_har_entries, resources):
            assert har_entry.request.url == resource.url
            assert resource.execution_ms == self.har.timings[resource.url].execution_ms
            assert resource.fetch_delay_ms == self.har.timings[resource.url].fetch_delay_ms
            assert resource.time_to_first_byte_ms == self.har.timings[resource.url].time_to_first_byte_ms
            if self.har.timings[resource.url].initiator == "":
                assert resource.initiator == 0
            else:
                assert resources[resource.initiator].url == self.har.timings[resource.url].initiator

    def test_har_entries_to_resources_ignores_non_http_and_non_complete(self):
        entries = []
        entry_urls = set()
        invalid_entries = set()
        for entry in self.har.log.entries:
            if random.random() < 0.1:
                new_url = entry.request.url
                new_status = entry.response.status
                if random.random() < 0.5:
                    new_url = "data:image/png;base64,asdflhqp49tqo3hifehqp" + str(random.random())[2:] + "=="
                else:
                    new_status = 0

                new_entry = HarEntry(
                    started_date_time=entry.started_date_time,
                    request=Request(url=new_url, method=entry.request.url),
                    response=Response(
                        status=new_status,
                        body_size=entry.response.body_size,
                        headers_size=entry.response.headers_size,
                        mime_type=entry.response.mime_type,
                    ),
                )
                entries.append(new_entry)
                invalid_entries.add(new_entry.request.url)
            else:
                entries.append(entry)
                entry_urls.add(entry.request.url)

        invalid_entries = invalid_entries - set(entry_urls)
        resources = har_entries_to_resources(Har(log=HarLog(entries=entries), timings={}))

        assert len(resources) < len(entries) - len(invalid_entries)
        assert not any(res.url in invalid_entries for res in resources)
        assert all(res.url in entry_urls for res in resources)
