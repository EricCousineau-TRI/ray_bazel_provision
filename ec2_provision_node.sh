#!/bin/bash
set -eux

sudo echo "Needs sudo auth"

# Ensure that we mark this explicitly as a ray node (so people don't break their
# own machines).
echo 'See my_code/README.md' \
    > ~/.this_is_a_ray_node

cd $(dirname ${BASH_SOURCE})
# Add --full-reinstall if hardware is reconfigured.
yes | sudo ./ec2_install_desktop_and_nvidia.sh

export DISPLAY=:0

./ec2_install_efs.sh
./ec2_install_my_code.sh
./ec2_install_nvtop.sh

# Disable annoying things.
sudo apt-get -y purge unattended-upgrades
# Purge unneeded packages.
sudo apt-get -y autoremove
# Remove cruft in AMI.
# TODO(eric.cousineau): Where does this even come from?
sudo rm -rf  /usr/local/lib/python?.?

# Build everything.
# - We may get a dumb "File exists". Just try rerunning a few times.
for i in $(seq 5); do
    bazel build //... -k
done

# Briefly test disk uage.
df -h /
