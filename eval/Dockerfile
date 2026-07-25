# Anti-Hackers RDT -- Linux testbed container with tc/netem
#
# Build (from the repo root):
#   docker build -t anti-hackers-testbed -f eval/Dockerfile .
#
# Run (from the repo root; NET_ADMIN lets tc/netem shape the container's own
# loopback interface -- it grants nothing outside this container):
#   docker run --rm -it --cap-add=NET_ADMIN -v "${PWD}:/app" anti-hackers-testbed
#
# Inside the container:
#   python -m pytest                      # sanity check (expect all tests passing)
#   python eval/run_experiments.py        # REAL kernel netem sweep (no --simulate-loss)
#
# Results land in eval/results.csv and eval/plots/ in your repo folder on the
# host, because the repo is volume-mounted.

FROM python:3.10-slim

# iproute2 provides `tc`; sudo lets eval/setup_netem.sh run unmodified
# (the container runs as root, so sudo is a no-op passthrough).
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps at build time so runs start instantly.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Headless matplotlib for plot generation inside the container.
ENV MPLBACKEND=Agg

CMD ["bash"]