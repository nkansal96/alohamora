def get_chrome_flags(user_data_dir):
  # https://peter.sh/experiments/chromium-command-line-switches/
  return ' '.join([
    '--allow-insecure-localhost',
    '--disable-background-networking',
    '--disable-default-apps',
    # '--disable-gpu',
    # '--disable-logging',
    # '--disable-renderer-backgrounding',
    # '--disable-threaded-animation',
    # '--disable-threaded-compositing',
    # '--disable-threaded-scrolling',
    # '--disable-threaded-animation',
    '--headless',
    '--ignore-certificate-errors',
    '--no-check-certificate',
    '--no-default-browser-check',
    '--no-first-run',
    '--user-data-dir={}'.format(user_data_dir),
  ])
