#!/usr/bin/env python3

"""
Formats first GPU's bus information for use with Xorg configuration.

For NVidia, see `nvidia-smi --help-query-gpu`
For Xorg, see https://www.x.org/releases/X11R7.7/doc/man/man5/xorg.conf.5.xhtml#heading10
"""

from subprocess import check_output


def hex2dec(s):
    return int(s, 16)


def main():
    raw = check_output(
        "nvidia-smi -i 0 --query-gpu=gpu_bus_id --format=csv,noheader",
        shell=True,
        text=True,
    ).strip()
    domain_bus_device, function = raw.split(".")
    _, bus, device = domain_bus_device.split(":")
    print(f"PCI:{hex2dec(bus)}:{hex2dec(device)}:{hex2dec(function)}")


assert __name__ == "__main__"
main()
