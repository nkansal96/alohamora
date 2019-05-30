#! /bin/bash

pip3 install virtualenv                   || exit 1
virtualenv -p python3.6 $(pwd)/.blaze_env || exit 1
source .blaze_env/bin/activate            || exit 1
pip install -r requirements.txt           || exit 1

pushd third_party/node && \
  npm install; \
popd
