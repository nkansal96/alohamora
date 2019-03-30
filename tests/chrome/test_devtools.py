from blaze.chrome.devtools import capture_har
from tests.mocks.config import get_config

class TestCaptureHar():
  def setup(self):
    self.config = get_config()

  def test_capture_har(self):
    har = capture_har('https://www.google.com', self.config)
    assert har
