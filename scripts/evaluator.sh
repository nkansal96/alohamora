#! /bin/bash

TRAIN_DIR=/home/nikhil/push-policy/training
OUTPUT_DIR=/home/nikhil/push-policy/results/$1
REWARD_FUNC=1

function run_eval() {
	checkpoint="$1"
	exp_name="$2"
	bandwidth="$3"
	latency="$4"
	cpu_slowdown="$5"
	manifest="${TRAIN_DIR}/${exp_name}.manifest"
	output_file="${OUTPUT_DIR}/${exp_name}_${bandwidth}kbps_${latency}ms_${cpu_slowdown}x"

	if [[ ! -f "$output_file" ]]; then
		echo ${checkpoint} ${exp_name}
		timeout --foreground 600 blaze evaluate \
			--model A3C \
			--location "${checkpoint}" \
			--manifest "${manifest}" \
			--reward_func "${REWARD_FUNC}" \
			--bandwidth "${bandwidth}" \
			--latency "${latency}" \
			--cpu_slowdown "${cpu_slowdown}" \
			--run_simulator \
			--run_replay_server > "${output_file}"
	else
		echo exists: ${output_file}
	fi
}

rm -rf /home/nikhil/ray_results/A3C*

for experiment_dir in /home/nikhil/ray_results/*; do
	latest_experiment=$(ls -td ${experiment_dir}/A3C* | head -n 1)
	exp_name=$(basename ${experiment_dir})
	checkpoint=$(ls -vdr ${latest_experiment}/checkpoint* | head -n 1)
	checkpoint_file=${checkpoint}/$(basename ${checkpoint} | tr '_' '-')
	run_eval ${checkpoint_file} ${exp_name} 24000 20 2
	run_eval ${checkpoint_file} ${exp_name} 12000 60 4
done
