#! /bin/bash

export MAHIMAHI_CERT_DIR=$(pwd)/../mahimahi/src/frontend/certs
export CHROME_HAR_CAPTURER_BIN=$(pwd)/tools/capture_har/capturer/run.js
export PWMETRICS_BIN=$(pwd)/tools/capture_har/node_modules/.bin/pwmetrics
export LOG_LEVEL=debug
