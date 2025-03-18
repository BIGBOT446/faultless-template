#!/bin/bash

if [ -f ".python-backend" ]
then
    export PYTHON_BACKEND=$(cat .python-backend)
else
    echo "Error: No .python-backend file found!"
    exit 1
fi
