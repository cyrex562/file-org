#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*"
}

# Update and install required dependencies
log "Updating package list and installing required dependencies..."
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

# Install pyenv if not already installed
if [ ! -d "$HOME/.pyenv" ]; then
    log "Installing pyenv..."
    curl https://pyenv.run | bash

    # Add pyenv to the shell startup script
    log "Configuring pyenv in shell startup script..."
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

    # Reload shell configuration
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"
else
    log "pyenv is already installed."
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"
fi

# Get the latest stable version of Python
log "Getting the latest stable version of Python..."
LATEST_PYTHON_VERSION=$(pyenv install -l | grep -E '^\s*[0-9\.]+$' | grep -v - | tail -1 | tr -d ' ')

# Install the latest Python version if not already installed
if ! pyenv versions --bare | grep -q "^${LATEST_PYTHON_VERSION}$"; then
    log "Installing Python $LATEST_PYTHON_VERSION..."
    pyenv install $LATEST_PYTHON_VERSION
fi

log "Setting global Python version to $LATEST_PYTHON_VERSION..."
pyenv global $LATEST_PYTHON_VERSION

# Define the project directory and virtual environment path
PROJECT_DIR="$(pwd)"
VENV_PATH="$PROJECT_DIR/.venv"

# Remove existing virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    log "Removing existing virtual environment..."
    rm -rf "$VENV_PATH"
fi

# Create a new virtual environment
log "Creating a new virtual environment in $VENV_PATH..."
python -m venv $VENV_PATH

# Activate the virtual environment
log "Activating the virtual environment..."
source $VENV_PATH/bin/activate

# Upgrade pip
log "Upgrading pip..."
pip install --upgrade pip

# Install required Python packages
log "Installing required Python packages..."
pip install click xxhash tqdm paramiko scp

# Inform the user
log "Setup is complete. The virtual environment is created in the project directory as .venv."
log "To activate the virtual environment, use: 'source $PROJECT_DIR/.venv/bin/activate'"