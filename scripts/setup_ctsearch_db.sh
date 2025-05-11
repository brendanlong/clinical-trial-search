#!/bin/bash
# Setup script for Clinical Trial Search database schema

set -euo pipefail

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker does not seem to be running. Please start Docker and try again."
  exit 1
fi

# Check if the database container is running
if ! docker ps | grep -q clinical-trial-postgres; then
  echo "Starting PostgreSQL database..."
  docker-compose up -d

  # Wait for PostgreSQL to initialize
  echo "Waiting for PostgreSQL to initialize..."
  sleep 5
fi

# Check if database exists
if ! docker exec clinical-trial-postgres psql -U postgres -lqt | grep -q aact; then
  echo "Error: The AACT database does not exist yet."
  echo "Please run the AACT data loading script first."
  exit 1
fi

echo "Creating the ctsearch schema and tables..."
docker exec -i clinical-trial-postgres psql -U postgres -d aact < "$(dirname "$0")/setup_ctsearch_db.sql"

# Verify the tables were created
echo "Verifying the schema was created successfully..."
TABLES=$(docker exec -i clinical-trial-postgres psql -U postgres -d aact -c '\dt ctsearch.*' | grep -c 'table')

if [[ $TABLES -gt 0 ]]; then
  echo "Success! The ctsearch schema was created with $TABLES tables."
else
  echo "Error: The ctsearch schema tables were not created properly."
  exit 1
fi

echo "Schema setup complete!"
