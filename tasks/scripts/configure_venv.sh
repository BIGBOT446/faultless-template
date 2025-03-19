#!/bin/bash

if [ "$PYTHON_BACKEND" == "pip" ]
then
    echo "Ensuring pip is installed..."
    output=$(python -m ensurepip 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Pip could not be installed."
        exit 1
    fi
    output=$(python -m pip install --upgrade pip 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: Pip could not be upgraded."
        exit 1
    fi

    echo "Ensuring pip-tools is installed..."
    output=$(python -m pip install --upgrade "pip-tools==7.4.1" 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: pip-tools could not be installed using pip."
        exit 1
    fi
fi
