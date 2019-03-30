import subprocess
import tempfile

from blaze.config import Config
from blaze.chrome.config import get_chrome_command, get_chrome_flags
from blaze.chrome.devtools import capture_har
from blaze.mahimahi import MahiMahiConfig

def record_webpage(url: str, save_dir: str, config: Config):
  with tempfile.TemporaryDirectory(prefix='blaze_record', dir='/tmp') as tmp_dir:
    chrome_flags = get_chrome_flags(tmp_dir)
    chrome_cmd = get_chrome_command(chrome_flags, url, config)

    mm_config = MahiMahiConfig(config)
    cmd = mm_config.record_shell_with_cmd(save_dir, chrome_cmd)

    proc = subprocess.run(cmd=cmd)
    proc.check_returncode()
