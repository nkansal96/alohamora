#! /bin/bash

export LOG_LEVEL=warn
export PUSH_POLICY_DIR=/home/nikhil/push-policy

MODEL=A3C
WORKERS=70
REWARD_FUNC=1
MANIFEST_DIR="${PUSH_POLICY_DIR}/training"
TRAIN_LOG_FILE="${PUSH_POLICY_DIR}/train.log"
TRAIN_MANIFESTS="${PUSH_POLICY_DIR}/train_manifests.txt"

cat ${TRAIN_MANIFESTS} | xargs -I "{}" blaze train "{}" \
					--model ${MODEL} \
					--workers ${WORKERS} \
					--reward_func ${REWARD_FUNC} \
					--manifest_file "${MANIFEST_DIR}/{}.manifest" \
					--no-resume >> ${TRAIN_LOG_FILE} 2>&1
