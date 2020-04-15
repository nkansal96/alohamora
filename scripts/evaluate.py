#! /usr/bin/env python3

import argparse
import concurrent.futures
import glob
import itertools
import os
import signal
import subprocess
import sys
import threading
import time
import traceback

MODEL = "A3C"


def monitor_process(cmd, timeout, output_file, error_file, max_retries=3):
    last_write = time.time()
    process_exit = False
    proc = None

    def read_stream(stream, of):
        nonlocal last_write
        for line in iter(stream.readline, ""):
            of.write(line)
            last_write = time.time()
            if process_exit:
                break

    def check_timeout():
        nonlocal last_write
        while not process_exit:
            if time.time() - last_write > timeout:
                print(f"[{time.time()} - {last_write}] Timed out: {cmd}")
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            time.sleep(5)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setpgrp)

    read_stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, output_file))
    read_stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, error_file))
    check_timeout_thread = threading.Thread(target=check_timeout)

    read_stdout_thread.start()
    read_stderr_thread.start()
    check_timeout_thread.start()

    try:
        retcode = proc.wait()
    except KeyboardInterrupt:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        raise
    finally:
        process_exit = True
        read_stdout_thread.join()
        read_stderr_thread.join()
        check_timeout_thread.join()

    if retcode != 0 and max_retries > 0:
        monitor_process(cmd, timeout, output_file, error_file, max_retries - 1)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", required=True, help="Directory to store the results in")
    parser.add_argument("--ray_results_dir", required=True, help="Directory of ray results to traverse")
    parser.add_argument("--manifests_dir", required=True, help="Directory of stored training manifests")
    parser.add_argument("--num_workers", default=4, type=int, help="Number of workers to use")

    parser.add_argument("--bandwidth", type=int, help="bandwidth to test with")
    parser.add_argument("--latency", type=int, help="latency to test with")
    parser.add_argument("--cpu_slowdown", type=int, choices=[1, 2, 4], help="cpu_slowdown to test with")
    parser.add_argument("--randomize", help="set this flag to randomly choose bw, latency and cpu", action="store_true")
    parser.add_argument(
        "--reward_func",
        required=True,
        type=int,
        choices=[0, 1, 2, 3],
        help="reward function that the model was trained with",
    )
    parser.add_argument("--warm_cache", action="store_true", help="use warm cache")
    parser.add_argument("--cache_time", type=int, help="seconds to expire cache")
    return parser.parse_args()


def get_test_websites(ray_results_dir):
    for experiment_name in os.listdir(ray_results_dir):
        if experiment_name.startswith(MODEL):
            continue
        experiment_dir = os.path.join(ray_results_dir, experiment_name)
        model_dirs = sorted(glob.glob(f"{experiment_dir}/{MODEL}*"))
        if len(model_dirs) == 0:
            continue

        latest_model = model_dirs[-1]
        checkpoint_dirs = sorted(glob.glob(f"{latest_model}/checkpoint*"), key=lambda d: int(d.split("_")[-1]))

        if len(checkpoint_dirs) == 0:
            continue

        latest_checkpoint = checkpoint_dirs[-1]
        latest_checkpoint_file = checkpoint_dirs[-1] + "/checkpoint-" + latest_checkpoint.split("_")[-1]

        yield latest_checkpoint_file, experiment_name


def get_results_fname(experiment_name, results_dir, bandwidth="", cpu_slowdown="", latency=""):
    return os.path.join(results_dir, experiment_name + str(bandwidth) + "_" + str(latency) + "_" + str(cpu_slowdown))


def website_exists(experiment_name, results_dir):
    return os.path.exists(get_results_fname(experiment_name, results_dir) + ".json")


def test_website(
    args, results_dir, manifests_dir, reward_func, bandwidth, cpu_slowdown, latency, checkpoint_file, experiment_name
):
    tempdir = None
    if args.warm_cache:
        tempdir = tempfile.mkdtemp(prefix="blaze_warm_" + os.path.basename(manifest_file).split(".manifest")[0])
    with open(
        get_results_fname(experiment_name, results_dir, bandwidth, cpu_slowdown, latency) + ".json", "ab+"
    ) as outf:
        with open(
            get_results_fname(experiment_name, results_dir, bandwidth, cpu_slowdown, latency) + ".log", "ab+"
        ) as errf:
            monitor_process(
                [
                    "blaze",
                    "evaluate",
                    "--model",
                    MODEL,
                    "--location",
                    checkpoint_file,
                    "--manifest",
                    os.path.join(manifests_dir, experiment_name) + ".manifest",
                    "--latency",
                    str(latency),
                    "--bandwidth",
                    str(bandwidth),
                    "--cpu_slowdown",
                    str(cpu_slowdown),
                    "--reward_func",
                    str(reward_func),
                    *(["--cache_time", str(args.cache_time)] if args.cache_time else []),
                    *(["--user_data_dir", tempdir] if tempdir else []),
                    "--run_simulator",
                    "--run_replay_server",
                ],
                60 * 10,
                outf,
                errf,
            )


def worker(args, results_dir, manifests_dir, reward_func, bandwidth, cpu_slowdown, latency, checkpoint_file, experiment_name):
    try:
        if website_exists(experiment_name, results_dir):
            print(f"evaluating {checkpoint_file} ... skipping (already exists)")
            return
        print(f"evaluating {checkpoint_file} ...")
        test_website(
            args, results_dir, manifests_dir, reward_func, bandwidth, cpu_slowdown, latency, checkpoint_file, experiment_name
        )
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()


def generate_random_params():
    bandwidth = list(range(12000, 24001, 2000))
    latency = list(range(20, 101, 20))
    cpu = [2, 4]
    return list(itertools.product(bandwidth, cpu, latency))


def main(args):
    if (not args.randomize) and (args.bandwidth is None or args.cpu_slowdown is None or args.latency is None):
        print("Either choose randomize option or provide all three of (bw, latency, cpu).")
        sys.exit(1)
    websites = list(get_test_websites(args.ray_results_dir))
    params = generate_random_params() if args.randomize else [(args.bandwidth, args.cpu_slowdown, args.latency)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as pool:
        f = [
            pool.submit(
                worker,
                args,
                args.results_dir,
                args.manifests_dir,
                args.reward_func,
                bandwidth,
                cpu_slowdown,
                latency,
                checkpoint_file,
                experiment_name,
            )
            for (checkpoint_file, experiment_name) in websites
            for (bandwidth, cpu_slowdown, latency) in params
        ]
        print("Finished processing", len([p.result() for p in f]), "websites")


if __name__ == "__main__":
    main(get_args())
