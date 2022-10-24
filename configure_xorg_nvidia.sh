#!/bin/bash

set -eux

# Reset nvidia things.
systemctl stop xorg.service || true
rmmod -f nvidia_uvm || true
rmmod -f nvidia_drm || true
rmmod -f nvidia_modeset || true
rmmod -f nvidia || true
nvidia-smi || true

# Call `modprobe` so that we can use the GPU. Otherwise, we can get a
# `THCudaCheck unknown error` failure in pytorch.
modprobe nvidia

# Record bus ID.
# TODO(eric.cousineau): Put in separate script.
cur_dir=$(dirname ${BASH_SOURCE})
bus_id=$(${cur_dir}/get_xorg_bus_id_from_nvidia.py)

# Start the X DISPLAY server.
systemctl stop xorg.service || true
cat <<EOF | tee /lib/systemd/system/xorg.service
[Unit]
Description=X Server
After=network.target

[Service]
ExecStart=/usr/bin/X :0

[Install]
WantedBy=multi-user.target
Alias=xorg.service
EOF
cat <<EOF | tee /etc/X11/xorg.conf
Section "ServerLayout"
    Identifier     "Layout0"
    Screen      0  "Screen0"
EndSection

Section "Files"
EndSection

Section "Monitor"
    Identifier     "Monitor0"
    VendorName     "Unknown"
    ModelName      "Unknown"
    HorizSync       28.0 - 33.0
    VertRefresh     43.0 - 72.0
    Option         "DPMS"
EndSection

Section "Device"
    Identifier     "Device0"
    Driver         "nvidia"
    VendorName     "NVIDIA Corporation"
    BusID          "${bus_id}"
EndSection

Section "Screen"
    Identifier     "Screen0"
    Device         "Device0"
    Monitor        "Monitor0"
    DefaultDepth    24
    Option         "AllowEmptyInitialConfiguration" "True"
    Option         "ConnectedMonitor" "none"
    SubSection     "Display"
        Depth       24
    EndSubSection
EndSection
EOF
systemctl reenable xorg.service
systemctl start xorg.service
