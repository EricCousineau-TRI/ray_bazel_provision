#!/bin/bash
set -eu

# Setup script to be used by ray cluster config files.
# Assumes we're using the correct AMI.

log_persist=
install_prereqs=
build_ray=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    # Store logs outside of /tmp (useful for debugging provisioning bugs).
    --log_persist)
      log_persist=1
      ;;
    # Run Anzu's install_prereqs, upgrade apt, and remove old things.
    --install_prereqs)
      install_prereqs=1
      ;;
    # Do not build `//tools:ray` initially.
    --no_build_ray)
      build_ray=
      ;;
    -h|--help)
      echo "Please read source"
      exit 0
      ;;
    *)
      echo 'Invalid command line argument' >&2
      exit 1
      ;;
  esac
  shift
done

if [[ ! -f ~/.this_is_a_ray_node ]]; then
    echo "Must only be run on Anzu ray nodes (via AWS AMI)." 2>&1
    exit 1
fi

set -x

# Symlink environment setup.
ln -sf ~/my_code/ray_env.sh ~/ray_env.sh
# - Use environment for this script.
source ~/ray_env.sh

# Ensure all interactive sessions (such as those from ray or via manual ssh)
# use our desired environment variables.
echo 'source ~/ray_env.sh' > ~/.bash_aliases

# Create binary shortcuts for `ray`.
cat > ~/.local/bin/ray <<'EOF'
#!/bin/bash
exec ~/my_code/run //tools:ray "$@"
EOF
chmod +x ~/.local/bin/ray

# If needed, update NVidia+Xorg configuration for the current instance's
# graphics card.
if ! glxinfo > /dev/null ; then
    echo "glxinfo failed; reconfiguring..."
    sudo ~/my_code/configure_xorg_nvidia.sh
fi

if [[ -n ${log_persist} ]]; then
    # Use this if you need logs to persist across restart (for debugging).
    ~/my_code/ray_log_persist.sh
fi

if [[ -n ${install_prereqs} ]]; then
    # Ensure Anzu's prereqs are up-to-date.
    yes | sudo ~/my_code/setup/install_prereqs.sh

    # Fix security holes.
    yes | sudo apt upgrade

    # Remove cruft.
    yes | sudo apt autoremove
fi

if [[ -n ${build_ray} ]]; then
    ( cd ~/my_code && bazel build //tools:ray )
fi
