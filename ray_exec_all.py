r"""
Executes commands on both head and worker nodes.

Example:

    ./ray_exec_all.py \
        /path/to/cluster_file.yaml \
        'ray stop || true'
"""

import argparse
import dataclasses as dc
from enum import Enum
from multiprocessing.pool import ThreadPool
from os.path import expanduser
import re
import shlex
from subprocess import PIPE, STDOUT, run
from textwrap import dedent, indent

from my_code.runfiles import Rlocation

RAY_BIN = Rlocation("my_code/ray")


def subshell(args, *, check=True):
    result = run(args, text=True, stdout=PIPE, stderr=STDOUT)
    if check and result.returncode != 0:
        print(result.stdout)
        raise RuntimeError(f"Error: {result.returncode}\n{args}")
    return result.stdout


@dc.dataclass
class Config:
    ssh_user: str
    ssh_key: str
    ssh_command: str
    ray_cluster: str
    process_count: int
    check_returncode: bool


class NodeType(Enum):
    Head = 0
    Worker = 1


def get_ray_ips(config: Config, node_type: NodeType):
    if node_type == NodeType.Head:
        subcommand = "get-head-ip"
    elif node_type == NodeType.Worker:
        subcommand = "get-worker-ips"
    else:
        assert False, node_type
    # Extracts IP addresses from output of `ray (get-head-ip|get-worker-ips)`.
    # A bit silly, but only way I (Eric) know how to do this.
    text = subshell([RAY_BIN, subcommand, config.ray_cluster], check=False)
    if "Head node of cluster" in text and "not found" in text:
        return None
    return re.findall(r"^(\d+\.\d+\.\d+\.\d+)$", text, flags=re.MULTILINE)


def get_ray_head_and_worker_ips(config: Config):
    # TODO(eric.cousineau): Find ray API for this.
    head_ips = get_ray_ips(config, NodeType.Head)
    if head_ips is None:
        return None
    assert len(head_ips) == 1
    worker_ips = get_ray_ips(config, NodeType.Worker)
    return head_ips + worker_ips


def bash_command_with_login(command: str, interactive: bool = False):
    # Ensures command is run as bash login shell (so ~/.bashrc is used).
    bash_opts = ["--login"]
    if interactive:
        bash_opts += ["-i"]
    return shlex.join(["bash"] + bash_opts + ["-c", command])


def ssh_exec(config: Config, host: str, use_tty: bool):
    # These were derived by inspecting ssh commands as indicated by from
    # `ray exec` commands.
    # TODO(eric.cousineau): Find ray API for this.
    ssh_opts = [
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        config.ssh_key,
        "-o",
        "LogLevel=ERROR",
        "-A",
    ]
    user_host = f"{config.ssh_user}@{host}"
    bash_command = bash_command_with_login(config.ssh_command, use_tty)

    ssh_common_fmt = dedent(config.ssh_command).strip()
    ssh_common_fmt = indent(ssh_common_fmt, "  ")
    ssh_common_fmt = "+" + ssh_common_fmt[1:]
    print(indent(ssh_common_fmt, f"[{host}] "))
    if use_tty:
        args = ["ssh", "-tt"] + ssh_opts + [user_host, bash_command]
        # TODO(eric.cousineau): This doesn't work well with Bazel.
        # Figure out how `ray exec` does it.
        run(args, check=config.check_returncode)
    else:
        args = ["ssh"] + ssh_opts + [user_host, bash_command]
        stdout = subshell(args, check=config.check_returncode).strip()
        print(indent(stdout, f"[{host}] "))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("cluster_file", type=str)
    parser.add_argument("ssh_command", type=str)
    parser.add_argument("--process_count", type=int, default=10)
    parser.add_argument("--tty", "-t", action="store_true")
    parser.add_argument("--keep_going", "-k", action="store_true")
    args = parser.parse_args()

    config = Config(
        ssh_user="ubuntu",
        ssh_key=expanduser("~/.ssh/my-key.pem"),
        ssh_command=args.ssh_command,
        ray_cluster=args.cluster_file,
        process_count=args.process_count,
        check_returncode=not args.keep_going,
    )

    ips = get_ray_head_and_worker_ips(config)
    if ips is None:
        print("Cluster not running")
        return
    print(f"ips: {ips}")
    with ThreadPool(config.process_count) as pool:
        func = lambda ip: ssh_exec(config, ip, args.tty)
        pool.map(func, ips)


assert __name__ == "__main__"
main()
