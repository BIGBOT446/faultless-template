#!/bin/bash

# Check if this branch is a release branch, i.e. it starts with "release/"
# If so, check it follows the correct format, i.e. "release/X.Y.Z".
# Also that the tag associated with the release branch doesn't already exist

branchname=$1

echo "Validating branch name: $branchname..."

# Check if the branch is a release branch
if [[ $branchname == release/* ]]
then
    # Fetch the latest tags
    output=$(git fetch --tags)
    if [[ $? -ne 0 ]]
    then
        echo "Error: Failed to fetch tags"
        exit 1
    fi

    # Check if the release branch follows a bad format, if so exit early
    if [[ $branchname =~ ^release/[0-9]+\.[0-9]+\.[0-9]+$ ]]
    then
        echo "Error: Release branch $branchname does not follow the correct format"
        exit 1
    fi

    # Check if the tag associated with the release branch already exists
    tagname=${branchname/release\//}
    if git rev-parse -q --verify "refs/tags/$tagname" > /dev/null
    then
        echo "Error: Tag $tagname already exists, cannot release this branch."
        exit 1
    fi
fi

echo "Branch name is valid"
