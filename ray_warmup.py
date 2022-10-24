"""
Script to warm up agents and test job submission.
"""
import argparse
import datetime
import subprocess
import time

import ray

import my_code.ray_bazel as ru


@ray.remote
def fake_work(i, duration):
    # Use `ru` to show that build commands, env vars, etc. propagate.
    ru.maybe_use_ray_head_pwd()
    # Nominal work.
    time.sleep(duration)
    completed_timestamp = (
        datetime.datetime.today()
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )
    print(f"job[{i}]: Completed {duration}s sleep @ {completed_timestamp}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local", action="store_true", help="If running in a local machine"
    )
    parser.add_argument("--num_jobs", "-n", type=int, help="Number of jobs")
    parser.add_argument(
        "--sleep_duration",
        type=float,
        default=5,
        help="Sleep duration (sec) for each fake_work job",
    )
    parser.add_argument(
        "--num_cpus", type=int, default=1, help="Number of CPUs per job",
    )
    parser.add_argument(
        "--num_gpus", type=int, default=0, help="Number of GPUs per job",
    )
    args = parser.parse_args()

    if args.local:
        ray.init(address="", include_dashboard=False)
    else:
        ray.init(
            address="auto",
            runtime_env=ru.ray_preserve_bazel_target_runtime_env(),
        )

    fake_work_conf = fake_work.options(
        num_gpus=args.num_gpus, num_cpus=args.num_cpus
    )

    print("Submit")
    ids = [
        fake_work_conf.remote(i, args.sleep_duration)
        for i in range(args.num_jobs)
    ]
    print("Gather")
    ray.get(ids)


if __name__ == "__main__":
    main()
