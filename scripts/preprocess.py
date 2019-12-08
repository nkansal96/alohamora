#! /usr/bin/env python3

import argparse
import concurrent.futures
import os
import re
import signal
import subprocess
import sys
import threading
import time
import traceback


def monitor_process(cmd, timeout, output_file, retries=3):
    last_write = time.time()
    process_exit = False
    proc = None

    def read_stream(stream):
        nonlocal last_write
        for line in iter(stream.readline, ""):
            output_file.write(line.decode())
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

    read_stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout,))
    read_stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr,))
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

    if retcode != 0 and retries > 0:
        monitor_process(cmd, timeout, output_file, retries - 1)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_dir", required=True, help="Directory containing the recorded websites")
    parser.add_argument(
        "--extract_critical_requests", action="store_true", help="Preprocess and additionally get critical requests"
    )
    parser.add_argument("--num_workers", default=4, type=int, help="Number of workers to use")
    return parser.parse_args()


def get_record_dirs(train_dir_location):
    return [d for d in os.listdir(train_dir_location) if os.path.isdir(os.path.join(train_dir_location, d))]


def get_manifest_file(train_dir_location, website_dir):
    return os.path.join(train_dir_location, f"{website_dir}.manifest")


def preprocess_website(train_dir_location, website_dir, extract_critical_requests):
    url = "https://" + website_dir.replace("__", "/")
    monitor_process(
        [
            "blaze",
            "preprocess",
            "--train_domain_globs",
            "*",
            *(["--extract_critical_requests"] if extract_critical_requests else []),
            "--record_dir",
            os.path.join(train_dir_location, website_dir),
            "--output",
            get_manifest_file(train_dir_location, website_dir),
            url,
        ],
        60 * 5,
        sys.stdout,
    )


def manifest_exists(train_dir_location, website_dir):
    return os.path.isfile(get_manifest_file(train_dir_location, website_dir))


def worker(train_dir_location, website_dir, extract_critical_requests):
    try:
        if manifest_exists(train_dir_location, website_dir):
            print(f"preprocessing {website_dir} ... skipping (already exists)")
            return
        print(f"preprocessing {website_dir} ... ")
        preprocess_website(train_dir_location, website_dir, extract_critical_requests)
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()


def main(args):
    train_dir_location = os.path.abspath(args.train_dir)
    record_dirs = get_record_dirs(train_dir_location)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as pool:
        f = [
            pool.submit(worker, train_dir_location, website_dir, args.extract_critical_requests)
            for website_dir in record_dirs
        ]
        print("Finished processing", len([p.result() for p in f]), "websites")


if __name__ == "__main__":
    main(get_args())
