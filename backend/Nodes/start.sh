#!/bin/bash
set -e

echo "Starting PostgreSQL..."
service postgresql start

sleep 3

echo "Initializing database if needed..."
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='cluster_db'\" | grep -q 1 || createdb cluster_db"

echo "Starting DB cluster node..."
python main.py
