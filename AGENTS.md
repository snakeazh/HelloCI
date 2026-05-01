# AGENTS.md

## Cursor Cloud specific instructions

This repository is a CI/CD pipeline demo/sandbox. It contains **no application code** — only CI configuration files:

- `.circleci/config.yml` — CircleCI pipeline (echoes messages in a Node 4.8.2 container)
- `.gitlab-ci.yml` — GitLab CI pipeline (two jobs: build and test stages, echo messages)
- `.travis.yml` — Travis CI pipeline (echoes messages, declared as `cpp` language)

### Key facts

- **No dependencies** to install (no `package.json`, `requirements.txt`, `Makefile`, etc.)
- **No services** to start or run
- **No tests** to execute (CI jobs only run `echo` commands)
- **No build step** required
- **No lint** configuration exists

### Development workflow

Editing this repo means modifying CI/CD YAML configs. Validate YAML syntax before committing. There is nothing to run locally — the CI configs are executed by their respective CI platforms (CircleCI, GitLab CI, Travis CI) when triggered by pushes.
