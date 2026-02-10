FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Core dev utilities (base image provides: git, curl, ca-certificates, sudo, vscode user)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bash-completion \
    vim \
    && rm -rf /var/lib/apt/lists/*
