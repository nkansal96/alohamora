from blaze.mahimahi.server.filestore import check_cacheability
from blaze.mahimahi.server.filestore import CACHE_CONTROL_HEADER, EXPIRES_HEADER, PRAGMA_HEADER, LAST_MODIFIED_HEADER


class TestCheckCacheability:
    def test_no_headers(self):
        assert not check_cacheability({})

    def test_not_cacheable(self):
        tests = [
            dict({CACHE_CONTROL_HEADER: "junk=123, max-age=0, junk4=1"}),
            dict({CACHE_CONTROL_HEADER: "junk=123, junk4=1, max-age=0"}),
            dict({CACHE_CONTROL_HEADER: "no-store, junk=123"}),
            dict({CACHE_CONTROL_HEADER: "junk=123, no-cache"}),
            dict({CACHE_CONTROL_HEADER: "junk=123, no-cache, max-age=123"}),
            dict({PRAGMA_HEADER: "no-cache"}),
            dict({EXPIRES_HEADER: "0"}),
            dict({EXPIRES_HEADER: "0", CACHE_CONTROL_HEADER: "max-age=0"}),
            dict({CACHE_CONTROL_HEADER: "max-age=asdf"}),
            dict({CACHE_CONTROL_HEADER: "max-age=asdf", EXPIRES_HEADER: "0"}),
        ]

        for test in tests:
            assert not check_cacheability(test), f"failed: {test}"

    def test_cacheable(self):
        tests = [
            dict({CACHE_CONTROL_HEADER: "max-age=123"}),
            dict({CACHE_CONTROL_HEADER: "max-age=asdf", EXPIRES_HEADER: "1600"}),
            dict({EXPIRES_HEADER: "1600"}),
            dict({LAST_MODIFIED_HEADER: "today"}),
            dict({LAST_MODIFIED_HEADER: "today", CACHE_CONTROL_HEADER: "max-age=asdf"}),
        ]

        for test in tests:
            assert check_cacheability(test), f"failed: {test}"
