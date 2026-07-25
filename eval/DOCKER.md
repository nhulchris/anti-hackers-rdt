# Docker netem testbed (Windows / macOS / any host)

This container gives the project a real Linux environment with `tc/netem`, so the
evaluation sweep can run with **kernel-level** packet loss and delay -- the testbed as
originally proposed -- from any host OS.

## One-time setup (Windows)
1. Install Docker Desktop (docker.com) and start it. Enable WSL 2 if prompted.
2. Verify: `docker --version`

## Build (from the repo root)