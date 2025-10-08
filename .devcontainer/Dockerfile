FROM python:3.11-bookworm

# Build environment variables
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    sudo && \
    apt-get clean

# Set up user
ARG USER=pydev
ENV PATH /home/${USER}/.local/bin:$PATH
RUN groupadd -r ${USER} && \
    useradd -m -r -s /bin/bash -g ${USER} ${USER} && \
    echo -n "${USER}:${USER}" | chpasswd && \
    echo "${USER} ALL = NOPASSWD: ALL" > /etc/sudoers.d/${USER} && \
    chmod 440 /etc/sudoers.d/${USER}

USER ${USER}

# Install additional python packages
RUN pip install --upgrade pip wheel setuptools tox pipx

# Install uv
RUN pipx install uv

USER root
