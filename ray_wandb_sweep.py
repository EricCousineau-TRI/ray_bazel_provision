"""
Script to start wandb sweep agents for use with ray cluster.

This script should generally be run on a head node of a ray cluster.

NOTE: You can use this script locally using the option `--local` with launching
an AWS cluster.
"""

import argparse
import os

import ray
import wandb
import yaml

import my_code.ray_bazel as ru


@ray.remote
def run_wandb_agent(sweep_id, project):
    ru.maybe_use_ray_head_pwd()
    # Ensure we can use `./run` via `wandb.agent()` -- same as what
    # `//tools:wandb` does.
    for key in ["RUNFILES_MANIFEST_FILE", "RUNFILES_DIR"]:
        if key in os.environ:
            del os.environ[key]
    try:
        wandb.agent(sweep_id, entity="tri", project=project)
    except wandb.errors.Error as e:
        if "Sweep" in str(e) and "is not running" in str(e):
            print(e)
            # N.B. We must do this to avoid interrupting existing runs.
            print("Ignoring failure b/c we assume this is an extra agent")
        else:
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sweep_config",
        type=str,
        default=None,
        nargs="?",
        help="Sweep config. Mutually exclusive to --sweep_id.",
    )
    parser.add_argument(
        "--sweep_id",
        type=str,
        default=None,
        help="Existing sweep id (for completing runs). Mutually exclusive to "
        "sweep_config.",
    )
    parser.add_argument("-p", "--wandb_project", type=str)
    parser.add_argument(
        "--num_agents", "-n", type=int, help="Number of sweep agents"
    )
    parser.add_argument(
        "--num_cpus",
        type=int,
        default=5,
        help="Number of CPUs per job (wandb agent)",
    )
    parser.add_argument(
        "--num_gpus",
        type=float,
        default=1.0,
        help="Number of GPUs per job (wandb agent)",
    )
    parser.add_argument(
        "--local", action="store_true", help="If running in a local machine"
    )
    args = parser.parse_args()

    assert bool(args.sweep_config) ^ bool(
        args.sweep_id
    ), "Must supply either sweep_config or --sweep_id"
    if args.sweep_config is not None:
        with open(args.sweep_config, "r") as f:
            sweep_config = yaml.safe_load(f)
        sweep_id = wandb.sweep(sweep=sweep_config, project=args.wandb_project)
    else:
        sweep_id = args.sweep_id

    if args.local:
        ray.init(address="", include_dashboard=False)
    else:
        ray.init(
            address="auto",
            runtime_env=ru.ray_preserve_bazel_target_runtime_env(),
        )

    worker = run_wandb_agent.options(
        num_cpus=args.num_cpus, num_gpus=args.num_gpus
    )
    ids = [
        worker.remote(sweep_id, args.wandb_project)
        for _ in range(args.num_agents)
    ]
    ray.get(ids)


if __name__ == "__main__":
    main()
