#! /bin/bash

export MAHIMAHI_CERT_DIR=$(pwd)/../mahimahi/src/frontend/certs
export CHROME_HAR_CAPTURER_BIN=$(pwd)/third_party/node/capture_har.js
export PWMETRICS_BIN=$(pwd)/third_party/node/node_modules/.bin/pwmetrics
export DEBUG=1

train_dir="$HOME/push-policy/training"

blaze preprocess \
	"https://www.amazon.com" \
	--record_dir "$train_dir/www.amazon.com" \
	--output "$train_dir/www.amazon.com.manifest" \
	--train_domain_globs "*amazon.com"
blaze preprocess \
	"https://www.wikipedia.org" \
	--record_dir "$train_dir/www.wikipedia.org" \
	--output "$train_dir/www.wikipedia.org.manifest" \
	--train_domain_globs "*wikipedia.org"
blaze preprocess \
	"https://www.reddit.com" \
	--record_dir "$train_dir/www.reddit.com" \
	--output "$train_dir/www.reddit.com.manifest" \
	--train_domain_globs "*reddit*"
blaze preprocess \
	"https://www.pinterest.com" \
	--record_dir "$train_dir/www.pinterest.com" \
	--output "$train_dir/www.pinterest.com.manifest" \
	--train_domain_globs "*pinterest*" "*pinimg*"
blaze preprocess \
	"https://www.bing.com" \
	--record_dir "$train_dir/www.bing.com" \
	--output "$train_dir/www.bing.com.manifest" \
	--train_domain_globs "*bing.com"
blaze preprocess \
	"https://www.cnn.com" \
	--record_dir "$train_dir/www.cnn.com" \
	--output "$train_dir/www.cnn.com.manifest" \
	--train_domain_globs "*cnn.com"
blaze preprocess \
	"https://www.apple.com" \
	--record_dir "$train_dir/www.apple.com" \
	--output "$train_dir/www.apple.com.manifest" \
	--train_domain_globs "*apple.com"
blaze preprocess \
	"https://www.buzzfeed.com" \
	--record_dir "$train_dir/www.buzzfeed.com" \
	--output "$train_dir/www.buzzfeed.com.manifest" \
	--train_domain_globs "*buzzfeed.com"
