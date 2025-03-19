#!/bin/bash

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip show pre-commit &> /dev/null)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip show pre-commit &> /dev/null)
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
    echo Installing pre-commit hooks...
    output=$(pre-commit install 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: pre-commit install failed. Please try again."
        exit 1
    fi
fi

if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip show nbstripout &> /dev/null)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip show nbstripout &> /dev/null)
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
    output=$(nbstripout --install 2>&1)
    if [ $? -ne 0 ]
    then
        echo "$output"
        echo "Error: nbstripout install failed. Please try again."
        exit 1
    fi
fi

if [ -f ".config.yaml.template" ] && [ ! -f ".config.yaml" ]
then
    echo "Creating .config.yaml file from template..."
    if ! cp .config.yaml.template .config.yaml
    then
        echo "Error: Failed to create .config.yaml from .config.yaml.template file"
        exit 1
    fi
fi

if [ ! -f ".vscode/settings.json" ]
then
    echo "Creating VS Code settings.json..."
    mkdir -p ".vscode"
    cp "./tasks/vscode/settings.template.json" ".vscode/settings.json"
fi
