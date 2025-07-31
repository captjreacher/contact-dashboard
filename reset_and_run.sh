#!/bin/bash
# This script resets the application environment by stopping containers,
# deleting the database, and rebuilding and restarting the services.

echo "Stopping and removing existing Docker containers..."
docker-compose down

echo "Removing old database file..."
rm -f data/db/app.db

echo "Building and starting the application..."
docker-compose up --build -d

echo "Application is starting. Check 'docker-compose logs -f' for logs."
