#!/bin/bash

echo "Ensuring project folder has a Git repository initialized..."
# Git is a pre-condition for using pyproject.toml with setuptools_scm
if [ ! -d ".git" ]; then
    echo "Error: No Git repository found!"
    exit 1
fi

echo "Updating requirements.txt ..."

# Development
if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip compile \
        --extra dev \
        --extra check \
        --extra test \
        --extra doc \
        --extra notebook \
        --extra profile \
        --extra viz \
        --output-file="requirements.txt" \
        "pyproject.toml" \
        2>&1)

    output=$(uv pip compile \
        --extra dev \
        --extra check \
        --extra test \
        --extra doc \
        --extra notebook \
        --extra profile \
        --extra viz \
        --python-platform=linux \
        --output-file="requirements-linux.txt" \
        "pyproject.toml" \
        2>&1)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip-compile \
        --extra dev \
        --extra check \
        --extra test \
        --extra doc \
        --extra notebook \
        --extra profile \
        --extra viz \
        --resolver=backtracking \
        --no-allow-unsafe \
        --unsafe-package=pywin32 \
        --unsafe-package=pip \
        --unsafe-package=distribute \
        --unsafe-package=setuptools \
        --output-file="requirements.txt" \
        --strip-extras \
        "pyproject.toml" \
        2>&1)
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
    echo "Error: Failed to update requirements.txt !"
    exit 1
fi

echo "Updating requirements-ci.txt ..."

# CI
if [ "$PYTHON_BACKEND" == "uv" ]
then
    output=$(uv pip compile \
        --extra check \
        --extra test \
        --python-platform=linux \
        --output-file="requirements-ci.txt" \
        "pyproject.toml" \
        2>&1)
elif [ "$PYTHON_BACKEND" == "pip" ]
then
    output=$(pip-compile \
        --extra check \
        --extra test \
        --resolver=backtracking \
        --no-allow-unsafe \
        --unsafe-package=pywin32 \
        --unsafe-package=pip \
        --unsafe-package=distribute \
        --unsafe-package=setuptools \
        --output-file="requirements-ci.txt" \
        --strip-extras \
        "pyproject.toml" \
        2>&1)
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
    echo "Error: Failed to update requirements-ci.txt !"
    exit 1
fi
