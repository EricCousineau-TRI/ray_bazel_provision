#!/bin/bash
set -eux

sudo echo "Needs sudo auth"

cd ~/my_code/
bash ./setup/gen_dotfiles_bazelrc.sh
yes | sudo ./setup/install_prereqs.sh
