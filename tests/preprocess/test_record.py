import random
import requests

import pytest
from unittest import mock


from blaze.preprocess.record import record_webpage, find_url_stable_set, get_page_links, STABLE_SET_NUM_RUNS
from tests.mocks.config import get_config
from tests.mocks.har import empty_har, generate_har, HarReturner


def exists_before(seq, a, b):
    a_i = seq.index(a)
    for b_i in range(a_i, len(seq)):
        if seq[b_i] == b:
            return True
    return False


def make_page_links(*links):
    html = """<html><body>{links}</body></html>"""
    link = """<a href="{}" />"""
    return html.format(links="".join(map(link.format, links)))


class TestRecordWebpage:
    def setup(self):
        self.config = get_config()

    @mock.patch("subprocess.run")
    def test_record_webpage(self, mock_run):
        url = "https://cs.ucla.edu"
        save_dir = "/tmp/save_dir"

        record_webpage(url, save_dir, self.config)
        call_args = mock_run.call_args[0][0]
        assert mock_run.called and mock_run.call_count == 1 and call_args

        assert call_args[0] == "mm-webrecord"
        assert save_dir in call_args
        assert self.config.chrome_bin in call_args
        assert url in call_args


class TestFindUrlStableSet:
    def setup(self):
        self.config = get_config()

    def test_handles_all_missing_har_files(self):
        hars = [empty_har() for _ in range(STABLE_SET_NUM_RUNS)]
        with mock.patch("blaze.preprocess.record.capture_har_in_mahimahi", new=HarReturner(hars)) as mock_capture_har:
            stable_set = find_url_stable_set("http://cs.ucla.edu", self.config)
        assert not stable_set

    def test_handles_some_missing_har_files(self):
        hars = [random.choice([generate_har(), empty_har()]) for _ in range(STABLE_SET_NUM_RUNS)]
        with mock.patch("blaze.preprocess.record.capture_har_in_mahimahi", new=HarReturner(hars)) as mock_capture_har:
            stable_set = find_url_stable_set("http://cs.ucla.edu", self.config)
        assert stable_set

    def test_find_url_stable_set(self):
        hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS)]
        har_urls = [[e.request.url for e in har.log.entries] for har in hars]
        with mock.patch("blaze.preprocess.record.capture_har_in_mahimahi", new=HarReturner(hars)) as mock_capture_har:
            stable_set = find_url_stable_set("http://cs.ucla.edu", self.config)
        # Ensure that all HARs were consumed
        assert mock_capture_har.i == STABLE_SET_NUM_RUNS
        # Ensure a non-empty stable set
        assert stable_set
        # Ensure that each element was present in all har files
        assert all(all(res.url in har for har in har_urls) for res in stable_set)
        # Ensure that the URLs are ordered correctly
        for i in range(len(stable_set)):
            for j in range(i + 1, len(stable_set)):
                # check that res[i] appears before each subsequent res[j] in har_files at least half
                # the time
                total = sum(exists_before(har, stable_set[i].url, stable_set[j].url) for har in har_urls)
                assert total >= len(hars) // 2


class TestGetPageLinks:
    def test_returns_empty_array_when_max_depth_reached(self):
        url = "http://cs.ucla.edu"
        links = get_page_links(url, max_depth=0)
        assert not links

    @mock.patch("requests.get")
    def test_returns_empty_if_request_status_not_200(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.RequestException()
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert not links

    @mock.patch("requests.get")
    def test_returns_empty_if_request_fails(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException()
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert not links

    @mock.patch("requests.get")
    def test_raises_if_nonrequest_related_exception_occurs(self, mock_get):
        mock_get.side_effect = RuntimeError()
        url = "http://cs.ucla.edu"
        with pytest.raises(RuntimeError):
            get_page_links(url)

    @mock.patch("requests.get")
    def test_returns_empty_if_empty_html_received(self, mock_get):
        mock_get.return_value.text = ""
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert not links

    @mock.patch("requests.get")
    def test_returns_empty_if_invalid_html_received(self, mock_get):
        mock_get.return_value.text = "<html><body></html>"
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert not links

    @mock.patch("requests.get")
    def test_returns_unique_links_in_order(self, mock_get):
        http_links = ["http://cs.ucla.edu/a", "http://cs.ucla.edu/b", "http://cs.ucla.edu/c"]
        html = make_page_links(*http_links, *http_links, *http_links)
        mock_get.return_value.text = html
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert links == http_links

    @mock.patch("requests.get")
    def test_ignores_non_http_links(self, mock_get):
        http_links = ["http://cs.ucla.edu/a", "http://cs.ucla.edu/b", "http://cs.ucla.edu/c"]
        non_http_links = [
            "ftp://b.com/test",
            "rss://a/feed",
            "data:image/gif;base64,R0lGODlhEAAJAIAAAP///wAAACH5BAEAAAAALAAAAAAQAAkAAAIKhI+py+0Po5yUFQA7",
        ]
        html = make_page_links(*http_links, *non_http_links)
        mock_get.return_value.text = html
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert links == http_links

    @mock.patch("requests.get")
    def test_ignores_links_to_another_domain(self, mock_get):
        ucla_links = ["http://cs.ucla.edu/a", "http://cs.ucla.edu/b", "http://cs.ucla.edu/c"]
        non_ucla_links = ["http://ucla.edu", "http://seas.ucla.edu", "http://stanford.edu"]
        html = make_page_links(*ucla_links, *non_ucla_links)
        mock_get.return_value.text = html
        url = "http://cs.ucla.edu"
        links = get_page_links(url)
        assert links == ucla_links

    @mock.patch("requests.get")
    def test_recursively_finds_http_links(self, mock_get):
        links_1 = ["http://cs.ucla.edu/a", "http://cs.ucla.edu/b", "http://cs.ucla.edu/c"]
        links_2 = ["http://cs.ucla.edu/d", "http://cs.ucla.edu/e", "http://cs.ucla.edu/f"]
        links_3 = ["http://cs.ucla.edu/g", "http://cs.ucla.edu/h", "http://cs.ucla.edu/i"]
        links_4 = ["http://cs.ucla.edu/j", "http://cs.ucla.edu/k", "http://cs.ucla.edu/l"]
        all_links = (links_1, links_2, links_3, links_4)
        all_htmls = [make_page_links(*links) for links in all_links]
        type(mock_get.return_value).text = mock.PropertyMock(side_effect=all_htmls)
        url = "http://cs.ucla.edu"
        links = get_page_links(url, max_depth=2)
        assert len(links) == sum(map(len, all_links))
        assert set(links) == set(sum(all_links, []))
