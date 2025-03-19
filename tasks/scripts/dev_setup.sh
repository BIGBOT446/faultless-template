#!/bin/bash

if [ ! -f "requirements.txt" ]
then
    echo "Error: No requirements.txt file found. Please generate one using dev_setup.sh and try again."
    exit 1
fi

source ./tasks/shims/create_dotenv
source ./tasks/shims/load_backend_env
source ./tasks/shims/install_backend
source ./tasks/shims/install_venv
source ./tasks/shims/activate_venv
source ./tasks/shims/configure_venv
source ./tasks/shims/sync_requirements
source ./tasks/shims/configure_project

echo Done!
