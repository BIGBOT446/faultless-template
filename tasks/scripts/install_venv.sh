#!/bin/bash

if command -v deactivate
then
    deactivate
fi

source ./tasks/shims/recover_corrupt_venv

# Finding Python version
if ! version=$(cat .python-version)
then
    echo "Error: No .python-version file found. Please create one and try again."
    exit 1
fi

# Checking if there is an existing virtual environment and which version it is
# Read the .venv/pyvenv.cfg file to get the Python version
if [ ! -f ".venv/pyvenv.cfg" ]
then
    source ./tasks/shims/install_new_venv
else
    if ! venv_version=$(python --version 2>&1 | grep -Po "\d+\.\d+\.\d+")
    then
        echo "Error: Could not read the Python version from the existing virtual environment."
        exit 1
    fi
    if [ "$venv_version" = "$version" ]
    then
        echo "Reusing existing virtual environment..."
    else
        # Checking if pyenv is installed
        output=$(command -v pyenv 2>&1)
        if [ $? -ne 0 ]
        then
            echo "$output"
            echo "Error: Pyenv is not installed. Please install it and try again."
            exit 1
        fi

        echo "Removing existing virtual environment using Python $venv_version"
        rm -rf .venv
        source ./tasks/shims/install_new_venv
    fi
fi
