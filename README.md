# Ray - Bazel Provisioning

Very loose example of custom-rolling things so you have full control over
aspects such as CUDA, X11, etc. Also has some utilities for use w/ Bazel.

Preferable over existing AWS images if you are OCD (like me) and/or need to
tune.

Extracted / scrubbed from TRI Anzu codebase.

## Provisioning Image

Consider using AWS Launch Templates to denote simplest starting point.

Then using Launch Template on base Ubuntu image, run following:

```
./ec2_provision_node.sh
```
