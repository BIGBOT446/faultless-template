#!/bin/bash

if [ ! -f "requirements.txt" ]
then
    echo "Error: Can't sync with requirements.txt since it doesn't exist!"
    exit 1
fi

echo "Syncing with requirements.txt file..."

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip sync requirements.txt 2>&1)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip-sync requirements.txt 2>&1)
elif [ -z "$PYTHON_BACKEND" ]
then
    echo "Error: No backend specified via PYTHON_BACKEND environment variable!"
    exit 1
else
    echo "Error: Unknown backend $PYTHON_BACKEND specified as PYTHON_BACKEND environment variable!"
    exit 1
fi
if [ $? -ne 0 ]
then
    echo "$output"
    echo "Error: Failed to sync with requirements.txt file."
    exit 1
fi
