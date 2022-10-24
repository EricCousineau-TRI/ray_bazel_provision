import os


def ray_preserve_bazel_target_runtime_env():
    """
    Tools to preseve a Bazel target's runtime environment. This relies on
    `bazel build` having been done *exactly* on head node as it is on worker
    nodes (at least relevant to the target).

    Otherwise, we may only get the environment from //tools:ray, which is *not*
    what we want.

    See also: https://docs.ray.io/en/releases-1.9.2/handling-dependencies.html#runtime-environments

    We explicitly do not use `working_dir`, as it may confusing to use.
    """  # noqa
    vars_to_keep = [
        "LD_LIBRARY_PATH",
        "PATH",
        "PYTHONPATH",
        "RUNFILES_DIR",
        "RUNFILES_MANIFEST_FILE",
    ]
    env = dict()
    for var in vars_to_keep:
        if var in os.environ:
            env[var] = os.environ[var]
    # See `maybe_use_ray_head_pwd()`.
    env["_ANZU_RAY_HEAD_PWD"] = os.getcwd()
    return dict(env_vars=env)


def maybe_use_ray_head_pwd():
    """
    Use this in worker jobs to ensure we preserve the PWD from head to worker
    nodes.

    `ray_preserve_bazel_target_runtime_env()` must have been used with
    `ray.init()` for the *cluster* case. Note that PWD seems to automatically
    propagate fine when using local ray resources.
    """
    # TODO(eric.cousineau): I do not know how to get ray to use working
    # directory in worker nodes as is used in head node. See
    # `ray_preserve_bazel_target_runtime_env()` for why we should avoid
    # `working_dir`, at least for use with my_code.
    cwd = os.environ.get("_ANZU_RAY_HEAD_PWD", None)
    if cwd is not None:
        os.chdir(cwd)
