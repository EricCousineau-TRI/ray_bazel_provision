#!/bin/bash

# Environment for use on ray cluster nodes.

if [[ ${0} == ${BASH_SOURCE} ]]; then
    echo "This should only be source'd." 2>&1
    exit 1
fi

if [[ ! -f ~/.this_is_a_ray_node ]]; then
    echo "Must only be run on Anzu ray nodes (via AWS AMI)." 2>&1
    # N.B. Use `return`, not `exit`, for `source`d scripts.
    return 1
fi

# Common environment variables for ray on AWS EC2.
export AWS_PROFILE=my-cluster
export DISPLAY=:0

# Denote to user that this is active.
if [[ -n "${PS1:-}" ]]; then
    export PS1="(my-ray) ${PS1}"
fi
