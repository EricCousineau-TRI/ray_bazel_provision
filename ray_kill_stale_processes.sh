#!/bin/bash
set -eu

if [[ ! -f ~/.this_is_a_ray_node ]]; then
    echo "Must only be run on Anzu ray nodes (via AWS AMI)." 2>&1
    exit 1
fi

maybe-kill() {
    if [[ $# -gt 0 ]]; then
        ( set -x; kill -9 "$@"; )
    else
        echo "No procs to kill"
    fi
}

# Attempts to kill "stale" processes that may have been left over from prior
# ray jobs. Should be used with `ray_exec_all`.

# These tend to be processes spawned by my_code, but excludes `ray` (for some
# reason).
maybe-kill $(set -x; pgrep -f my_code/bazel-bin/)

# TODO(eric.cousineau): I don't know what these are, but they eat up memory and
# cause CPU + GPU OOM errors.
maybe-kill $(set -x; pgrep -f "python3 -Wignore -c from multiprocess")

maybe-kill $(set -x; pgrep -f "ray::IDLE")
