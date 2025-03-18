#!/bin/bash

source ./tasks/shims/create_dotenv
source ./tasks/shims/load_backend_env
source ./tasks/shims/install_backend
source ./tasks/shims/install_venv
source ./tasks/shims/activate_venv
source ./tasks/shims/configure_venv
source ./tasks/shims/compile_requirements
source ./tasks/shims/sync_requirements
source ./tasks/shims/configure_project

echo Done!
