#! /bin/bash

eval_results_dir="$HOME/push-policy/eval_results_dir"
manifest_dir="$HOME/push-policy/training"
model_dir="$HOME/push-policy/models"

blaze train \
	"$1" \
	--dir "$model_dir/$1.model" \
	--cpus 48 \
	--model A3C \
	--manifest_file "$manifest_dir/$1.manifest" \
	--eval_results_dir "$eval_results_dir"
