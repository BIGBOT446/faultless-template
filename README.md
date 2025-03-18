# Faultless: AI-Powered Proofreader for Engineering Reports

<!-- badges: start -->
![Python Version](<https://img.shields.io/badge/python-3.12.7-green>)
[![Confluence](<https://img.shields.io/badge/wiki-confluence-blue>)](<https://tonkintaylor.atlassian.net/wiki/spaces/PPP/pages/1422196737>)
![Licence](<https://img.shields.io/badge/licence-proprietary-red>)
[![Ruff](<https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff>)
[![pre-commit](<https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit>)
[![SonarQube](<https://img.shields.io/badge/code_analysis-SonarQube-lightgrey>)](<https://tonkintaylor-sonarqube.azurewebsites.net/dashboard?id=tonkintaylor_py-faultless-template_fc9da0e6-8d82-4eb7-bb9d-c81c6497408a>)

[![Jira](<https://img.shields.io/badge/tasks-jira-blue>)](<https://tonkintaylor.atlassian.net/browse/CAPSTONE>)
<!-- badges: end -->

## Introduction

An AI-powered review engine for engineering reports used in the development and maintenance of buildings, roads, bridges, and tunnels. It acts as a virtual senior engineer by scanning and marking drafts for structural clarity, compliance with standards, and overall accuracy, enabling quick revisions.

Job number: YYYTTNZ.0730

## Getting Started on Development

### Installing the Python environment and Configuring VS Code

Run the following command in Windows Powershell to configure the environment and
your VS Code settings (your current directory should be the root of the repo):

```Powershell
./tasks/dev_sync.ps1
```

## Other Development Tasks

### Adding a dependency (or regenerating the requirements files.)

Add a lowercase name of the package to the [project].dependencies section of the
`pyproject.toml` file. You will then need to re-generate the requirements files and
install the package via:

```Powershell
./tasks/dev_sync.ps1
```

### Releasing a package version

Run the following command in Windows Powershell to release a new version of the package:

```Powershell
./tasks/release.ps1
```

The branch will be automatically created and pushed to BitBucket, ready for a PR to be
created.

## Adding to changelog

Add a new file at `doc/whatsnew/{issue_num}.{entry_type}.rst` where `{issue_num}` is
the JIRA issue number being worked on, and `{entry_type}` is one of `feature`, `bugfix`,
`doc`, `removal`, `newhome`, `test`, or `devconfig`.

In the file provide a description of the change that will appear in the changelog.
