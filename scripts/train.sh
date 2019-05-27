#! /bin/bash

export MAHIMAHI_CERT_DIR=$(pwd)/../mahimahi/src/frontend/certs
export CHROME_HAR_CAPTURER_BIN=$(pwd)/third_party/node/capture_har.js
export PWMETRICS_BIN=$(pwd)/third_party/node/node_modules/.bin/pwmetrics
export DEBUG=1

eval_results_dir="$HOME/push-policy/eval_results_dir"
manifest_dir="$HOME/push-policy/training"
model_dir="$HOME/push-policy/models"

blaze train \
	"$1" \
	--dir "$model_dir/$1.model" \
	--cpus 8 \
	--model PPO \
	--manifest_file "$manifest_dir/$1.manifest" \
	--eval_results_dir "$eval_results_dir"
