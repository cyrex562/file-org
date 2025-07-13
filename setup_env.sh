#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update and install required dependencies
sudo apt update
sudo apt install -y \
    build-essential \
    curl \
    libbz2-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    zlib1g-dev \
    git \
    tmux \
    python3-venv

# Install pyenv
curl https://pyenv.run | bash

# Add pyenv to the shell startup script
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Reload shell configuration
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

# Install Python using pyenv
PYTHON_VERSION=3.10.4
pyenv install $PYTHON_VERSION
pyenv global $PYTHON_VERSION

# Create a virtual environment in the project directory
PROJECT_DIR="$(pwd)"
python -m venv $PROJECT_DIR/.venv

# Activate the virtual environment
source $PROJECT_DIR/.venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install click xxhash tqdm paramiko scp

# Inform the user
echo "Setup is complete. The virtual environment is created in the project directory as .venv."
echo "To activate the virtual environment, use: 'source $PROJECT_DIR/.venv/bin/activate'"