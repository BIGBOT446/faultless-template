#!/bin/bash

if [ "$PYTHON_BACKEND" == "uv" ]
then
    echo "Ensuring uv is installed at the latest version..."

    export PATH="$PATH:$HOME/.local/bin"
    # Legacy install support < v0.5.0
    export PATH="$PATH:$HOME/.cargo/bin"

    if ! command -v uv &> /dev/null || ( [ -z "$CI" ] && ! uv self update --quiet )
    then
        echo "Installing the latest version of uv..."

        if [ -n "$WINDIR" ]
        then
            # If in Windows
            if command -v pwsh &> /dev/null
            then
                output=$(pwsh -Command "irm https://astral.sh/uv/install.ps1 | iex" 2>&1)
            elif command -v powershell &> /dev/null
            then
                output=$(powershell -Command "irm https://astral.sh/uv/install.ps1 | iex" 2>&1)
            else
                output=$(C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "irm https://astral.sh/uv/install.ps1 | iex" 2>&1)
            fi
        else
            # Otherwise, assume in Linux
            output=$(curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1)
        fi
        if [ $? -ne 0 ]
        then
            echo "$output"
            echo "Error: Failed to install the latest version of uv"
            exit 1
        fi
    fi
fi
