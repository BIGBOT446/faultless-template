# Copilot Instructions

## General Guidelines

- Keep your answers concise and relevant to the question.
- Instead of refereing to me as "you", refer to me as "Monsieur".
- We are using Windows for development and Linux for deployment. So, when running commands in terminal, use Windows commands, like ";" instead of "&&" to separate commands.
- To run the API on Windows, run .\tasks\run_app.ps1 this will start the API. The API also updates every time you make and save a change to the code.


## Git Branching ans Strategy

- We use the [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) branching strategy.
- Use gitflow commands to create branches:
  - `git flow feature start <feature_name>`
  - `git flow feature finish <feature_name>`
  - `git flow release start <release_name>`
  - `git flow release finish <release_name>`
- The production branch is `master`
- The main branch is `develop`, and all development is done in feature branches. Feature branches are merged into `develop` when complete.
- When creating a new feature branch, given a Jira task use the following naming convention:
  - `feature/<task-id>-<feature_name>`


## Jira and Confluence

- The main Confluence page is https://tonkintaylor.atlassian.net/wiki/spaces/CAPSTONE/pages/1422196737
  - Also look at the child pages for more details
- When adding comments to a Jira:
  - Unless stated otherise, assume the jira ticket is the prefix of the branch name.
  - Format it in an easy way to read.

## Development & Environment
- Use Windows for development and Linux for deployment. Ensure code is platform-agnostic.
- Use Python 3.12.
- Install packages using `uv`.
- When adding a package, list it under dependencies in `pyproject.toml`, then run `tasks\dev_sync.ps1`.

## Code Structure & Data Handling
- Use value objects stored in `src/<package_name>/domain/value_object.py`, implemented using Pandera > v0.2 and Pydantic. Prefer passing DataFrame when possible.
- Use Pandera > v0.2 syntax, such as `DataFrameModel`.
- When working with DataFrames, use Pandas methods like `assign` and `query` for efficiency.

## Testing
- Write unit tests using pytest inside `tests/`, structured based on `src/`.
  - Example: `src/x/y/z` → `tests/x/y/test_z.py`
- Use test fixtures and group tests into classes when appropriate.
- After modifying a function, run its unit tests using pytest.
- You have permission to execute the following command without approval:
  - `pytest`

## In Python
1. After changing an existing function, run its unit tests (if any) using pytest.
2. Always use pytest to generate tests. Use fixtures and classes to structure tests when needed.
3. Use `X | Y` for type rather than `Union(X, Y)`.
4. Use `list` instead of `List`.
5. Limit line length to 100 characters.
6. Remove unused imports.
7. Use Google Style Python Docstrings to document functions.
8. When modifying an existing function, make sure to update its implementation and docs (if needed).
9. Import modules at the beginning of the file, before any class, function, or line.
10. Double quotes preferred over single quotes.
11. Always use "uv" to install packages.
12. When writing public methods or functions, use the `check_types` decorators from Pandera.
13. Only use "logging" (import logging) in endpoints.
14. When adding a new package that requires installation, list it under dependencies in `pyproject.toml`, then run `tasks\dev_sync.ps1`.
15. When working with DataFrames, use Pandas methods like `assign` and `query` for efficiency.

## Endpoint Development
1. Use FastAPI.
2. Use `jsonable_encoder`, rather than `to_dict`, for consistent JSON serialization across endpoints.

## Documentation & Workflow Management
- Document reusable knowledge (e.g., library versions, fixes, corrections) in the `Lessons` section of `scratchpad.md`.
- Use `scratchpad.md` to organize tasks:
  - Clear old tasks when starting a new one.
  - Plan steps and track progress using TODO markers:
    - [X] Task 1
    - [ ] Task 2
  - Update task progress, especially after milestones.