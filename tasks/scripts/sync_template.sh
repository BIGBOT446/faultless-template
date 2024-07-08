echo "Ensuring dependencies are installed..."

# Check whether pyenv is installed
output=$(command -v pyenv)
if [[ -z $output ]]
then
    echo $output
    echo "Error: pyenv could not be found"
    echo "Please install pyenv and try again"
    exit
fi

# Check whether git is installed
output=$(command -v git)
if [[ -z $output ]]
then
    echo $output
    echo "Error: git could not be found"
    echo "Please install git and try again"
    exit
fi

# Install pip, and then copier
output=$(python -m ensurepip)
if [[ -z $output ]]
then
    echo $output
    echo "Error: pip could not be installed in your currently activated python installation"
    exit
fi
output=$(python -m pip install pip --upgrade)
if [[ -z $output ]]
then
    echo $output
    echo "Error: pip could not be upgraded in your currently activated python installation"
    exit
fi
output=$(python -m pip install "copier >= 9.1.1" --upgrade)
if [[ -z $output ]]
then
    echo "Error: copier >= 9.1.1 could not be installed in your currently activated python installation"
    exit
fi

template_url="https://bitbucket.org/tonkintaylor/python-template"
tmpdir="$HOME/.ttpytemplatetemp"

# Copy the git repo to a temp directory
rm -rf $tmpdir
if ! git clone --depth 1 -b master $template_url $tmpdir
then
    echo "Error: Could not clone the template repository"
    rm -rf $tmpdir
    exit
fi

# check whether the .copier/.copier-answers.yml already exists, if so we should update
# otherwise just call copier directly
if [ -f ".copier/.copier-answers.yml" ]
then
    if ! python -m copier update "$tmpdir\src\main" --trust
    then
        echo "Error: Could not update from the template repository"
        rm -rf $tmpdir
        exit
    fi
else
    if [ -f "README.md" ]; then
        rm README.md
    fi
    if ! python -m copier copy "$tmpdir\src\main" . --trust
    then
        echo "Error: Could not copy the template repository"
        rm -rf $tmpdir
        exit
    fi
fi

rm -rf $tmpdir
