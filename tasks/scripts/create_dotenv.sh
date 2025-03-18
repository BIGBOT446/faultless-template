#!/bin/bash

# Create the .env file from the template
env_file=".env"
if [ ! -f "$env_file" ]
then
    echo "Ensuring .env file exists..."
    if ! env_template_content=$(cat ".env.template")
    then
        echo "Error: Failed to read .env.template file"
        exit 1
    fi
    if [ -z "$PWD" ]
    then
        echo "Error: Failed to get current working directory"
        exit 1
    fi

    # Replace the placeholder with the current working directory denoted by
    # ${YourWorkSpaceHere} in the .env.template file. If not present, we will
    # skip without an error.
    if [ -n "$WINDIR" ]
    then
        output=$(command -v cygpath 2>&1)
        if [ $? -ne 0 ]; then
            echo "$output"
            echo "Error: Failed to find cygpath command."
            exit 1
        fi
        wd=$(cygpath --mixed "$PWD")
    else
        wd="$PWD"
    fi
    if ! env_file_content="${env_template_content//\$\{YourWorkSpaceHere\}/$wd}"
    then
        echo "Error: Failed to replace ${YourWorkSpaceHere} placeholder in .env.template file"
        exit 1
    fi

    if ! echo "$env_file_content" > "$env_file"
    then
        echo "Error: Failed to write to .env file"
        exit 1
    fi
fi
