#!/bin/bash

# Provisions a vanilla AWS EC2 Ubuntu 20.04 Server AMI instance.
# Derived from Anzu setup stuff

set -eux

die () {
    echo "$@" 1>&2
    trap : EXIT  # Disable line number reporting; the "$@" message is enough.
    exit 1
}

at_exit () {
    echo "${me} has experienced an error on line ${LINENO}" \
        "while running the command ${BASH_COMMAND}"
}

cat_without_comments() {
    sed -e 's|#.*||g;' "$(dirname $0)/$1"
}

extra_apt_flags=

# Run `apt-get install` on the arguments, then clean up.
apt_install () {
  apt-get -q install ${extra_apt_flags} --no-install-recommends "$@"
  apt-get -q clean
}

me="ec2_install_desktop_and_nvidia"

# Check for root.
[[ "${EUID}" -eq 0 ]] || die "${me} must run as root. Please use sudo."

while [[ $# -gt 0 ]]; do
  case $1 in
    --full_reinstall)
      # TODO(eric.cousineau): Figure out more minimal patch to fix why
      # some EC2 instances no longer can launch `Xsession`.
      extra_apt_flags="--purge --reinstall"
      shift
      ;;
    *)
      die "Invalid arguments: $@"
      ;;
  esac
done

# Check for nvidia hardware.
if ! (set +o pipefail; lspci | grep -q NVIDIA); then
  echo "ERROR: There does not appear to be any NVidia hardware here."
  exit 1
else
  echo "OK: NVidia hardware found."
fi

# Disable cron-based upgrades; they're annoying.
# WARNING: Be sure to `apt upgrade` every so often!
apt-get purge unattended-upgrades

# Check for supported versions.
apt-get update -y
apt_install lsb-release apt-transport-https ca-certificates gnupg wget
ubuntu_release_yymm=$(lsb_release -sr)
ubuntu_codename=$(lsb_release -sc)
[[ "${ubuntu_release_yymm}" == "20.04" ]] ||
    die "${me} only supports Ubuntu 20.04."

# Install APT dependencies.
# (We do them piecewise to minimize our download footprint.)
apt_install $(cat_without_comments ec2_packages_desktop.txt)

version_to_install=470
apt_install \
  nvidia-driver-${version_to_install} \
  xserver-xorg-video-nvidia-${version_to_install} \
  libnvidia-cfg1-${version_to_install} \
  libnvidia-common-${version_to_install} \
  libnvidia-compute-${version_to_install} \
  libnvidia-decode-${version_to_install} \
  libnvidia-extra-${version_to_install} \
  libnvidia-encode-${version_to_install} \
  libnvidia-fbc1-${version_to_install} \
  libnvidia-gl-${version_to_install} \
  libnvidia-ifr1-${version_to_install} \
  nvidia-compute-utils-${version_to_install} \
  nvidia-dkms-${version_to_install} \
  nvidia-kernel-source-${version_to_install} \
  nvidia-utils-${version_to_install}

cur_dir=$(dirname ${BASH_SOURCE})
${cur_dir}/configure_xorg_nvidia.sh

# TODO(eric.cousineau, michel.hidalgo): Set up `x11vnc` server + `Xsession`
# binaries as a simple service?

echo "${me}: success"
