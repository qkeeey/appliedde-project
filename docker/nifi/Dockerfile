FROM apache/nifi:2.8.0

USER root
RUN mkdir -p /nifi/output && chown -R nifi:nifi /nifi
RUN apt-get update && apt-get install -y --no-install-recommends python3-requests && rm -rf /var/lib/apt/lists/*
USER nifi
