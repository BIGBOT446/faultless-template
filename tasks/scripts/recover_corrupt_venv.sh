#!/bin/bash

# Sometimes the virtual environment gets corrupted. This script will try to recover it
# without having to delete it and create a new one.

# There are many ways a virtual environment can get corrupted, but the main way is that
# temp folders get created (starting with a tilde/~) and then pip gives warnings/errors
# about partially installed/incorrectly installed packages. This script will remove
# those temp folders.

if [ ! -d ".venv" ]
then
    # No need to recover if there is no virtual environment
    return 0
fi

# If in windows
if [ -n "$WINDIR" ]
then
    sitePackagesPath=".venv/Lib/site-packages"
else
    venvLibPath=".venv/lib/"

    if ! folders=$(ls $venvLibPath)
    then
        echo "Error: Failed to list directories in lib folder in virtual environment"
        exit 1
    fi

    if [ $(echo "$folders" | wc -l) -ne 1 ]
    then
        echo "Error: Found more than one folder in lib folder in virtual environment"
        exit 1
    fi

    # Get the one folder
    folder=$(echo "$folders" | head -n 1)
    sitePackagesPath="$venvLibPath/$folder/site-packages"
fi

if ! directories=$(ls $sitePackagesPath)
then
    echo "Error: Failed to list directories in site-packages folder in virtual environment"
    exit 1
fi

for directory in $directories
do
    if [[ $directory == ~* ]]
    then
        echo "Found corrupted temp folder in virtual environment: $directory"
        echo "Removing..."
        rm -rf "$sitePackagesPath/$directory"
    fi
done
