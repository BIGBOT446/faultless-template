#!/bin/bash

source ./tasks/shims/load_backend_env
source ./tasks/shims/activate_venv

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip show towncrier &> /dev/null)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip show towncrier &> /dev/null)
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
    echo "Building the changelog using towncrier..."

    # Read the version from .latest-pkg-version
    next_release=$(cat .latest-pkg-version)

    if [ -z "$next_release" ]
    then
        echo "Error: Failed to read the release version from .latest-pkg-version !"
        exit 1
    fi

    output=$(python -m towncrier build --yes --version $next_release)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Failed to build the changelog with Towncrier!"
        exit 1
    fi

    echo "Built Changelog!"
fi
