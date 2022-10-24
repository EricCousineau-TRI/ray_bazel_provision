#!/bin/bash
set -eux

if [[ ! -f ~/.this_is_a_ray_node ]]; then
    echo "Must only be run on Anzu ray nodes (via AWS AMI)." 2>&1
    exit 1
fi

# See: https://github.com/ray-project/ray/issues/22707
# TODO(eric.cousineau): Use official / public recommendation. --temp-dir is
# possible, but there other issues with it, as mentioned in issue.
old_log_dir=/tmp/ray
new_log_dir=~/ray-logs
if [[ ! -L ${old_log_dir} ]]; then
    if [[ -d ${old_log_dir} && -d ${new_log_dir} ]]; then
        echo "Shouldn't already exist!" >&2
        exit 1
    fi

    if [[ ! -d ${old_log_dir} ]]; then
        mkdir -p ${old_log_dir}
    fi

    if [[ -d ${old_log_dir} ]]; then
        mv ${old_log_dir} ${new_log_dir}
    else
        mkdir -p ${new_log_dir}
    fi

    ln -s ${new_log_dir} ${old_log_dir}
fi
