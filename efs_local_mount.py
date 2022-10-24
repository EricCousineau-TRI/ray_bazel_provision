#!/usr/bin/env python3

"""
Mounts AWS EFS file system (to share with EC2 instances).

In order:

- Checks if apt packages needs to be installed
- Tries to umount needed directories
- Checks if a UID / GUID redirect is needed (see below for more info)
- Mounts the required directories

**WARNING**: If you typically put your machine to sleep (e.g. a laptop), and
you do not have consistent TRI connectivity (e.g. VPN), please note that your
machine could hang when resuming from sleep. To avoid this, consuder using the
--unmount_only option before sleeping. If your machine hangs on resume, then
use Ctrl+Alt+FN (where N is 1..7), login, and run this script.
"""

import argparse
import os
from os.path import expanduser, isdir, isfile
import shlex
from subprocess import DEVNULL, PIPE, STDOUT
from subprocess import run as _run
import sys

# User-visible directory.
EFS_DIR = expanduser("~/efs")

# For UID / GUID redirect via bindfs.
EFS_BINDFS_SOURCE_DIR = expanduser("~/.efs_bindfs_source")

# SECRET. Fill out yourself.
EFS_IP = "FILL"

# By default, EFS mount wants the user to be 1000, which may not be the case.
NEEDED_UID = 1000

BINDFS_TARGET_USER = os.getlogin()


def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def run(args, *, shell=False, **kwargs):
    assert not shell
    cmd = shlex.join(args)
    eprint(f"+ {cmd}")
    return _run(args, **kwargs)


def capture(args, *, shell=False, stderr=STDOUT, check=True, **kwargs):
    return run(
        args,
        stdout=PIPE,
        stderr=stderr,
        check=check,
        text=True,
        shell=shell,
        **kwargs,
    )


def which(prog):
    return run(["which", prog], stdout=DEVNULL).returncode == 0


def maybe_unmount(mount_text, d, mount_type, *, force):
    is_mounted = f" on {d} type {mount_type} (" in mount_text
    if is_mounted:
        print(f"Unmount {mount_type}: {d}")
        args = ["sudo", "umount"]
        if force:
            # Use --force for possibly detached NFS.
            # Use --lazy to prevent hangup.
            args += ["--force", "--lazy"]
        args += [d]
        run(args, check=True)
    return is_mounted


def maybe_unmount_all(force):
    text = capture(["mount"]).stdout
    maybe_unmount(text, EFS_DIR, "fuse", force=force)
    maybe_unmount(text, EFS_BINDFS_SOURCE_DIR, "nfs4", force=force)
    maybe_unmount(text, EFS_DIR, "nfs4", force=force)


def efs_mount(src_ip, target_dir):
    # See: https://docs.aws.amazon.com/efs/latest/ug/efs-onpremises.html
    print(f"EFS Mount: {target_dir}")
    if not isdir(target_dir):
        os.mkdir(target_dir)
    run(
        [
            "sudo",
            "mount",
            "-t",
            "nfs",
            "-o",
            "nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport",  # noqa
            f"{src_ip}:/",
            target_dir,
        ],
        check=True,
    )


def is_maybe_ray_node():
    return isfile(expanduser("~/.this_is_a_ray_node"))


def needs_uid_redirect_via_bindfs(uid):
    if os.getuid() != uid:
        return True
    else:
        return False


def bindfs_mount(src_dir, src_user, target_dir, target_user):
    print(f"bindfs mount: {target_dir}")
    if not isdir(target_dir):
        os.mkdir(target_dir)
    target_user = os.getlogin()
    run(
        [
            "sudo",
            "bindfs",
            f"--map={src_user}/{target_user}:@{src_user}/@{target_user}",
            src_dir,
            target_dir,
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--unmount_only", action="store_true")
    parser.add_argument("-f", "--force_unmount", action="store_true")
    args = parser.parse_args()

    if is_maybe_ray_node():
        eprint("Should only be run on local machines")
        sys.exit(1)

    if "SUDO_USER" in os.environ:
        eprint("Do not run this via sudo")
        sys.exit(1)

    apt_packages = []
    if not which("bindfs"):
        apt_packages += ["bindfs"]
    if not which("nfsidmap"):
        apt_packages += ["nfs-common"]
    if len(apt_packages) > 0:
        run(["sudo", "apt-get", "install"] + apt_packages, check=True)

    maybe_unmount_all(args.force_unmount)

    if args.unmount_only:
        return

    if needs_uid_redirect_via_bindfs(NEEDED_UID):
        print(f"User {BINDFS_TARGET_USER} id={os.getuid()} != {NEEDED_UID}")
        print(f"  Needs UID redirect using bindfs")
        # Mount vanilla EFS, which may not show correct user (and thus get
        # permission errors).
        efs_mount(EFS_IP, EFS_BINDFS_SOURCE_DIR)
        # Now mount with remapping of UID and GID.
        source_user = capture(["id", "-nu", str(NEEDED_UID)]).stdout.strip()
        bindfs_mount(
            EFS_BINDFS_SOURCE_DIR, source_user, EFS_DIR, BINDFS_TARGET_USER,
        )
    else:
        print("Direct mount")
        efs_mount(EFS_IP, EFS_DIR)


assert __name__ == "__main__"
try:
    main()
    print("[ Done ]")
except KeyboardInterrupt:
    pass
