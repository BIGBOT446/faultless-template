# Check whether pyenv is installed
if ! command -v pyenv &> /dev/null
then
    echo "pyenv could not be found"
    echo "Please install pyenv and try again"
    exit
fi

# Install pip, and then copier
python -m ensurepip
python -m pip install pip --upgrade
python -m pip install copier --upgrade


template_url="https://bitbucket.org/tonkintaylor/python-template"

# check whether the .copier/.copier-answers.yml already exists, if so we should update
# otherwise just call copier directly
if [ -f ".copier/.copier-answers.yml" ]; then
    python -m copier update "git+$template_url" --UNSAFE
else
    python -m pip install pre-commit --upgrade
    python -m pre_commit uninstall
    if [ -f "README.md" ]; then
        rm README.md
    fi
    python -m copier copy "git+$template_url" . --UNSAFE
fi
