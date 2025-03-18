#!/bin/bash

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip show build &> /dev/null)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip show build &> /dev/null)
elif [ -z "$PYTHON_BACKEND" ]
then
    echo "Error: No backend specified via PYTHON_BACKEND environment variable!"
    exit 1
else
    echo "Error: Unknown backend $PYTHON_BACKEND specified as PYTHON_BACKEND environment variable!"
    exit 1
fi
if [ $? -eq 0 ]
then
    output=$(python -m build 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Failed to build project!"
        exit 1
    fi
else
    echo "Error: The package 'build' is not installed!"
    exit 1
fi
