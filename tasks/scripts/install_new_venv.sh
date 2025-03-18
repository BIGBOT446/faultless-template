#!/bin/bash

echo "Ensuring Python $version is installed..."
if [ -z "$CI" ]; then
    if ! pyenv install $version &> /dev/null
    then
        echo "Python $version is not installed. Installing..."
        output=$(pyenv update 2>&1)
        if [ $? -ne 0 ]
        then
            echo "$output"
            echo "Error: Pyenv could not be updated."
            exit 1
        fi
        output=$(pyenv install $version 2>&1)
        if [ $? -ne 0 ]
        then
            echo "$output"
            echo "Error: Python $version could not be installed with Pyenv."
            exit 1
        fi
    fi
    output=$(pyenv shell $version 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Python $version could not be activated as the Pyenv version."
        exit 1
    fi
else
    # Check the version of Python matches
    output=$(python -V | grep $version 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Python $version is not installed. Please install it and try again."
        exit 1
    fi
fi

echo "Creating virtual environment..."
if [ -d .venv ]
then
    if ! rm -rf .venv
    then
        echo "Error: Existing virtual environment folder could not be deleted."
        exit 1
    fi
fi

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv venv 2>&1)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(python -m venv .venv 2>&1)
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
    echo "Error: Virtual environment could not be created."
    exit 1
fi
