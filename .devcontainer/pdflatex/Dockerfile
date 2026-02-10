FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Core dev utilities + TeX Live (cached in Docker layer since ~2GB)
# Retry loop works around transient 403s from Ubuntu mirrors during BuildKit builds
RUN apt-get update \
    && for i in 1 2 3; do \
        apt-get install -y --no-install-recommends --fix-missing \
            build-essential \
            bash-completion \
            vim \
            texlive-latex-base \
            texlive-fonts-recommended \
            texlive-latex-extra \
            texlive-fonts-extra \
            texlive-extra-utils \
        && break || { echo "Attempt $i failed, retrying..."; apt-get update; }; \
    done \
    && rm -rf /var/lib/apt/lists/*
