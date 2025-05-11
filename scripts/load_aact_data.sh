#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data/raw"
DUMP_FILE="postgres.dmp"
CONTAINER_NAME="clinical-trial-postgres"

echo "Starting PostgreSQL container..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d

echo "Waiting for PostgreSQL to be ready..."
while ! docker exec "$CONTAINER_NAME" pg_isready -U postgres > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL to start..."
  sleep 2
done

echo "Finding latest AACT dataset..."
LATEST_DATASET=$(find "$DATA_DIR" -name "aact_dataset_*.zip" -type f | sort -r | head -n 1)

if [ -z "$LATEST_DATASET" ]; then
  echo "Error: No AACT dataset found in $DATA_DIR"
  exit 1
fi

DATASET_FILENAME=$(basename "$LATEST_DATASET")
echo "Using dataset: $DATASET_FILENAME"

echo "Extracting PostgreSQL dump file..."
if [ ! -f "$DATA_DIR/$DUMP_FILE" ]; then
  unzip -j "$LATEST_DATASET" "$DUMP_FILE" -d "$DATA_DIR"
fi

echo "Loading AACT data into PostgreSQL..."
docker exec -i "$CONTAINER_NAME" pg_restore \
  --clean --if-exists \
  --no-owner --no-privileges \
  -U postgres -d aact \
  < "$DATA_DIR/$DUMP_FILE"

echo "Data loading complete!"
echo "You can now connect to the database with:"
echo "  docker exec -it $CONTAINER_NAME psql -U postgres -d aact"
