from blaze.mahimahi.server.filestore import check_cacheability
from blaze.mahimahi.server.filestore import CACHE_CONTROL_HEADER, EXPIRES_HEADER, PRAGMA_HEADER, LAST_MODIFIED_HEADER


class TestCheckCacheability:
    def test_no_headers(self):
        assert not check_cacheability({})

    def test_not_cacheable(self):
        tests = [
            {CACHE_CONTROL_HEADER: "junk=123, max-age=0, junk4=1"},
            {CACHE_CONTROL_HEADER: "junk=123, junk4=1, max-age=0"},
            {CACHE_CONTROL_HEADER: "no-store, junk=123"},
            {CACHE_CONTROL_HEADER: "junk=123, no-cache"},
            {CACHE_CONTROL_HEADER: "junk=123, no-cache, max-age=123"},
            {PRAGMA_HEADER: "no-cache"},
            {EXPIRES_HEADER: "0"},
            {EXPIRES_HEADER: "0", CACHE_CONTROL_HEADER: "max-age=0"},
            {CACHE_CONTROL_HEADER: "max-age=asdf"},
            {CACHE_CONTROL_HEADER: "max-age=asdf", EXPIRES_HEADER: "0"},
        ]

        for test in tests:
            assert not check_cacheability(test), f"failed: {test}"

    def test_cacheable(self):
        tests = [
            {CACHE_CONTROL_HEADER: "max-age=123"},
            {CACHE_CONTROL_HEADER: "max-age=asdf", EXPIRES_HEADER: "1600"},
            {EXPIRES_HEADER: "1600"},
            {LAST_MODIFIED_HEADER: "today"},
            {LAST_MODIFIED_HEADER: "today", CACHE_CONTROL_HEADER: "max-age=asdf"},
        ]

        for test in tests:
            assert check_cacheability(test), f"failed: {test}"
