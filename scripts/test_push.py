#! /usr/bin/env python3

import argparse
import concurrent.futures
import os
import re
import signal
import subprocess
import threading
import time
import traceback


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
    parser.add_argument(
        "--test_type", required=True, choices=["push", "push_preload", "preload"], help="The test type to run"
    )
    parser.add_argument("--manifests_file", required=True, help="Line-delimited file of paths to manifests to test")
    parser.add_argument("--results_dir", required=True, help="Directory to store the results in")
    parser.add_argument("--num_workers", default=4, type=int, help="Number of workers to use")

    parser.add_argument("--bandwidth", required=True, type=int, help="bandwidth to test with")
    parser.add_argument("--latency", required=True, type=int, help="latency to test with")
    parser.add_argument("--cpu_slowdown", required=True, type=int, choices=[1, 2, 4], help="cpu_slowdown to test with")
    parser.add_argument("--iterations", required=True, type=int, help="number of policies to try")
    parser.add_argument("--max_retries", required=True, type=int, help="maximum number of times to retry a failure")
    return parser.parse_args()


def get_test_websites(manifests_file):
    with open(manifests_file, "r") as f:
        return [line.strip() for line in f if line.strip()]


def get_results_fname(manifest_file, results_dir):
    manifest_fname = os.path.basename(manifest_file).split(".manifest")[0]
    return os.path.join(results_dir, manifest_fname)


def website_exists(manifest_file, results_dir):
    return os.path.exists(get_results_fname(manifest_file, results_dir) + ".json")


def test_website(args, manifest_file):
    with open(get_results_fname(manifest_file, args.results_dir) + ".json", "ab+") as outf:
        with open(get_results_fname(manifest_file, args.results_dir) + ".log", "ab+") as errf:
            monitor_process(
                [
                    "blaze",
                    "test_push",
                    "--policy_type",
                    args.test_type,
                    "--latency",
                    str(args.latency),
                    "--bandwidth",
                    str(args.bandwidth),
                    "--cpu_slowdown",
                    str(args.cpu_slowdown),
                    "--iterations",
                    str(args.iterations),
                    "--max_retries",
                    str(args.max_retries),
                    "--from_manifest",
                    manifest_file,
                ],
                60 * 10,
                outf,
                errf,
            )


def worker(args, manifest_file):
    try:
        if website_exists(manifest_file, args.results_dir):
            print(f"evaluating {args.test_type} for {manifest_file} ... skipping (already exists)")
            return
        print(f"evaluating {args.test_type} for {manifest_file} ... ")
        test_website(args, manifest_file)
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()


def main(args):
    websites = get_test_websites(args.manifests_file)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as pool:
        f = [pool.submit(worker, args, manifest_file) for manifest_file in websites]
        print("Finished processing", len([p.result() for p in f]), "websites")


if __name__ == "__main__":
    main(get_args())
