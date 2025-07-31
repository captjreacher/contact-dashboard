#!/bin/sh

# Run the given command if provided, otherwise start the server
if [ "$1" = "gunicorn" ] || [ "$1" = "" ]; then
    echo "Starting Gunicorn..."
    exec gunicorn -b 0.0.0.0:5000 src.main:app
else
    echo "Running custom command: $@"
    exec "$@"
fi
