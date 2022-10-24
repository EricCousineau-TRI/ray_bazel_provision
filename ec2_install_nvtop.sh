#!/bin/bash
set -eux

if [[ -f ~/.local/bin/nvtop ]]; then
    echo "Already installed"
    exit 0
fi

sudo echo "Needs sudo auth"
yes | sudo apt-get install cmake libncurses5-dev libncursesw5-dev

cd ~
git clone https://github.com/Syllo/nvtop
cd ~/nvtop
mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=~/.local/opt/nvtop
make -j install
mkdir -p ~/.local/bin
ln -s ~/.local/opt/nvtop/bin/nvtop ~/.local/bin/nvtop
