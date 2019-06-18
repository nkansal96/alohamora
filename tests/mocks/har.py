import datetime
import os
from types import SimpleNamespace

import numpy as np

from blaze.chrome.har import har_from_json, Har, HarLog, HarEntry

HAR_JSON_FILE = os.path.join(os.path.dirname(__file__), "data/www.reddit.com.har")
HAR_JSON = open(HAR_JSON_FILE, "r").read()


def get_har_json():
    return HAR_JSON


def generate_har():
    har_file = har_from_json(get_har_json())
    har_entries = []
    # randomly drop about 3% of entries
    for entry in har_file.log.entries:
        if np.random.random() > 0.03 or entry.request.url == "https://www.reddit.com/":
            har_entries.append(entry)

    # randomly swap some entries with 3% chance
    # don't swap the first few though
    for i in range(10, len(har_entries)):  # pylint: disable=consider-using-enumerate
        if np.random.random() < 0.03:
            swap_index = max(0, i - np.random.geometric(0.30))
            har_entries[i], har_entries[swap_index] = har_entries[swap_index], har_entries[i]

    # rewrite startedDateTime so that the entries are in order
    last_date = datetime.datetime.now()
    for (i, entry) in enumerate(har_entries):
        last_date += datetime.timedelta(milliseconds=np.random.randint(0, 1000))
        har_entries[i] = HarEntry(
            started_date_time=last_date,
            request=entry.request,
            response=entry.response,
        )

    return Har(
        log=HarLog(entries=har_entries),
        timings=har_file.timings,
    )


def empty_har():
    return Har(log=HarLog(entries=[]), timings={})


class HarReturner:
    def __init__(self, hars):
        self.hars = hars
        self.i = 0

    def __call__(self, url, config):
        if self.i >= len(self.hars):
            raise IndexError("capture_har called too many times!")
        har = self.hars[self.i]
        self.i += 1
        return har
