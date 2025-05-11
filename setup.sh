#!/bin/bash -e

uv sync

# Install pre-commit hooks
pre-commit install

echo "Setup complete!"
