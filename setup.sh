#!/bin/bash -e


# Install pre-commit hooks
pre-commit install

echo "Setup complete! You can now use:"
echo "  bin/fitbit-data.py - Fetch Fitbit data"
echo "  bin/sheets-upload.py - Interact with Google Sheets"