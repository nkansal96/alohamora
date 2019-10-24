#! /bin/bash

pip3 install virtualenv                        || exit 1
python3 -m virtualenv -p python3.6 .blaze_env  || exit 1
source .blaze_env/bin/activate                 || exit 1
pip install -r requirements.txt                || exit 1

pushd tools/capture_har && \
  npm install; \
popd
