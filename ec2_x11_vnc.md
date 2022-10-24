# AWS EC2, X11 Remote Desktop Server, Hardware Accel

**Goals**:

- Do whatever to get a permissibly licensed X11 server running that
doesn't kludge NVidia driver things (e.g. OpenGL, CUDA, all the fancy things)
- Do whatever to allow a VNC client to connect from AWS Workspace (running Windows) to an AWS EC2 instance running above stuff. (Don't try to do crazy Docker-in-Windows-with-CUDA stuff.)

## References

- <https://forums.developer.nvidia.com/t/nvidia-driver-vnc-and-glx-issue/59708/2> <br/>
  Learned about `x11vnc` here
- <https://github.com/LibVNC/x11vnc> <br/>
  For tips on SSH tunneling
- <https://ubuntu.com/tutorials/ubuntu-desktop-aws#3-configuring-the-vnc-server> <br/>
  Learned about running `/etc/X11/Xsession` here.
- Based on Anzu setup code

See base README for instructions.

**WARNING**:

* You will need to supply **your own** credentials!

## General Setup: Host and Remote Machine

* **host**: the machine you're physically working on
* **remote**: in this case, the AWS EC2 instance

```sh
# [ Host ]
# - Connect to remote. Replace <opts> with what you need.
# - For me (Eric), my `<opts>` are `-A -i ${my_pem}`
#     `-A` is forwarding SSH credentials (see `man ssh`) for GitHub, etc.
#     `-i ${my_pem}` for permissions, where `my_pem` is set in bash
ssh <opts> ubuntu@<ip>
# [ Remote ]
sudo apt update && sudo apt upgrade && sudo apt install tmux git
cd ~
git clone .../my_code.git
# Disonnect.
# - Reconnect, but with a `screen` session. In this case, I use tmux with some
# special config.
ssh <opts> \
    ubuntu@<ip> \
    -L 5900:localhost:5900 \
    -t 'env DISPLAY=:0 tmux'

# The `-L 5900:localhost:5900` allows us to port-forward VNC (see below for
# Remmina example).
# The `-t` tells ssh that we're running an interactive terminal.
# The `env DISPLAY=:0` tells our session that we're using the *remote* display;
# we're *not* trying to do X11 forwarding.

# [ Remote ]
# Setup xorg, nvidia, ubuntu desktop, x11vnc, and some other stuff.
# Install x11vnc.
cd ~/my_code
yes | sudo ./ec2_install_desktop_and_nvidia.sh --full_reinstall

# WARNING: If Xsession crashes (returns immediately), then you should re-run
# the above steps, then reboot your instance, reconnect, and rerun.

# [ Remote ]
# Confirm NVidia is in there
glxinfo | head -n 5

# [ Remote ]
# Run the server remotely.
x11vnc -localhost -display :0

# [ Remote ]
# Launch nominal X11 session.
# TODO(eric): Get rid of weird "Getting Started" and color mgmt crap?
/etc/X11/Xsession

# [ Host ]
# Run your VNC client, for example, Remmina.
# Settings for Remmina, adding new connectioon:
# - Protocol: VNC
# - Server: localhost
# - Color depth: 24bpp (may need to adjust)
# - Quality: Medium (may need to adjust)
remmina
# WARNING: Stuff may crash sometimes. :shrug:

# [ Remote ]
# Try out random applications.
xeyes
glxgears
gnome-terminal
```

### Misc. Settings

```sh
# Disable animations.
gsettings set org.gnome.desktop.interface enable-animations false
# Disable screen saver.
gsettings set org.gnome.desktop.session idle-delay 0
# Set initial screen resolution.
xrandr -s 1280x960
```

Some inconvenieces (could be solved at some point):

- When starting session, can complain:
  "Authentication is required to create a color managed device" (via `gksudo`).
  Just ignore.
