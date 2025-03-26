# Faultless: AI-Powered Proofreader for Engineering Reports

<!-- badges: start -->
![Python Version](<https://img.shields.io/badge/python-3.12.7-green>)
[![Confluence](<hhttps://tonkintaylor.atlassian.net/wiki/spaces/CAPSTONE/pages/1422196737>)
![Licence](<https://img.shields.io/badge/licence-proprietary-red>)
[![Ruff](<https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff>)
[![pre-commit](<https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit>)
[![SonarQube](<https://img.shields.io/badge/code_analysis-SonarQube-lightgrey>)](<https://tonkintaylor-sonarqube.azurewebsites.net/dashboard?id=tonkintaylor_py-faultless-template_fc9da0e6-8d82-4eb7-bb9d-c81c6497408a>)

[![Jira](<https://img.shields.io/badge/tasks-jira-blue>)](<https://tonkintaylor.atlassian.net/browse/CAPSTONE>)
<!-- badges: end -->

## Subsystem Overview

### ONLYOFFICE Docs

- [ONLYOFFICE Docs API documentation](https://api.onlyoffice.com/docs/docs-api/get-started/basic-concepts/)
- [Apache OpenOffice Developer's Guide](https://wiki.openoffice.org/wiki/Documentation/DevGuide)

### Langfuse

The `quick_start_example.py` script demonstrates how to integrate ***Langfuse*** with ***LangChain*** to perform grammar and spelling checks using Google Gemini. To use this script, ensure the following environment variables are set in your `.env` file:

- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `GOOGLE_API_KEY`

Additionally, while the default LLM configuration in `llm.yml` can be modified, we recommend keeping it unchanged during development as Google provides free API calls to a robust LLM model.

## Description

### Situation
Ensuring the accuracy and compliance of engineering reports is crucial for maintaining safe, sustainable infrastructure across Aotearoa. These reports guide the development and upkeep of buildings, roads, bridges, and tunnels, directly impacting communities and the environment.

Currently, senior technical engineers manually review reports for clarity, compliance with ISO standards, and structural soundness. However, this process is slow and depends on a small pool of highly experienced experts. By streamlining reviews with AI-powered pre-checks, we can accelerate infrastructure projects, reduce bottlenecks, and allow senior engineers to focus on higher-level decisions that shape resilient, future-ready communities.

### Problem
- The bottleneck in report processing arises because experienced engineers are in short supply.
- Reviews involve multiple iterations, often requiring revisions and feedback loops.
- Reviewers focus on structural clarity, adherence to standards, and technical accuracy, which could be partially automated to reduce their workload.
- Current manual review processes are inefficient and inconsistent.

### Opportunities
- Implement an automated report review system to check for clarity, structure, and compliance before senior engineers conduct final reviews.
- Use a rule-based approach, similar to [software linters](https://docs.astral.sh/ruff/linter/), to flag issues and provide suggestions before human intervention.

### Solution
- **Automated Report Review System**: Develop an AI-driven tool to review reports before they reach senior engineers, identifying common issues and improving efficiency.
- **Structured Review Process**: Implement a system where reports are annotated with suggested changes in a Word document, enabling engineers to accept or reject recommendations.
- **Version Control & Metrics**: Track report quality over time, similar to version control in coding, to monitor improvements or recurring issues.

## System Design

### During Development
- Sequence Diagram for developing, testing, and storing prompts.

### During Deployment
- Sequence Diagram of the automated Report Review System.
- Context Diagram of the automated Report Review System.

### Definitions
- **Faultless**: The name of the **Automated Report Review System**.
- **Laptop**: The user’s device, responsible for **uploading documents for review** and **downloading the reviewed document** after processing is complete.
- **Integration Hub**: The **central orchestrator** that manages document processing, coordinating interactions between all subsystems, storing analysis results, and ensuring smooth data flow.
- **Rule Engine**: Processes documents by **applying validation rules** in the form of prompts fetched from the **Prompt Management System (PMS)** and sending them to **AI Agents** for analysis.
- **Prompt Management System (PMS)**: A system responsible for **storing and managing prompts (rules)** used by the **Rule Engine** to guide AI-based document analysis.
- **AI Agents**: AI-powered components that **evaluate documents based on provided prompts**, performing tasks such as language checks, structural validation, and compliance assessments, and returning structured results.
- **Database**: Stores **document analysis results**, enabling data persistence for later retrieval, audits, or additional processing.
- **Document Server**: The system responsible for **modifying the document**, adding **comments, annotations, and tracked changes** based on analysis results before returning it for review.

## Development Strategy

Doing the right thing for the business right now > Doing the optimal thing

First make it work, then make it right, and, finally, make it fast. (In that order!)

1. **Make It Work [correctly]:** First crank out code that handles one common case.
2. **Make it Right**: Fix all salient special cases, error handling, etc. so all tests pass.
3. **Make it [become] Fast [later]**: Find and eliminate waste in the process. Some assumptions from the start will have been incorrect. Remove unnecessary business logic. Included in this step is to improve code for better performance, especially if speed is a requirement.

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


