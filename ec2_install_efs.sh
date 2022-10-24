#!/bin/bash
set -eux

if mount | grep "on /mnt/fs1/efs type nfs4"; then
    echo "Already mounted"
    exit 0
fi

sudo echo "Needs sudo auth"
# https://docs.ray.io/en/latest/cluster/aws-tips.html#using-amazon-efs
# https://docs.aws.amazon.com/efs/latest/ug/efs-mount-helper.html
sudo apt-get -y install binutils

cd ~
git clone https://github.com/aws/efs-utils
cd ~/efs-utils
./build-deb.sh
sudo apt-get -y install ./build/amazon-efs-utils*deb

efs_id=FILL

sudo mkdir -p /mnt/fs1/efs
sudo mount -t efs ${efs_id}:/ /mnt/fs1/efs
# Inspect directory to ensure it's mounted.
ls /mnt/fs1
# Enable automount.
echo "${efs_id}:/ /mnt/fs1/efs efs _netdev,tls 0 0" |
    sudo tee --append /etc/fstab
# Double check that it mounts.
sudo umount /mnt/fs1/efs
sudo mount -a
ls /mnt/fs1

# Make symlink
ln -s /mnt/fs1/efs ~/efs

# Use shared Bazel cache.
cd ~/.cache/
ln -sf ~/efs/shared_cache/bazel_external_data ./
ln -sf ~/efs/shared_cache/bazel_local_disk ./
ln -sf ~/efs/shared_cache/bazel-externals ./
