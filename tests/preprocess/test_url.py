from blaze.preprocess.url import Url


class TestUrl:
    def test_parse(self):
        url_str = "http://cs.ucla.edu/staff/index.html?t=15789123000"
        url = Url.parse(url_str)
        assert url.scheme == "http"
        assert url.domain == "cs.ucla.edu"
        assert url.resource == "/staff/index.html?t=15789123000"
        assert url.url == url_str

    def test_parse_no_resource(self):
        url_str = "http://cs.ucla.edu"
        url = Url.parse(url_str)
        assert url.scheme == "http"
        assert url.domain == "cs.ucla.edu"
        assert url.resource == "/"
        assert url.url == url_str + "/"
