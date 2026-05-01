# AGENTS.md

## Cursor Cloud specific instructions

This repository (`HelloCI`) is a minimal CI/CD configuration demo. It contains **no application code, no dependencies, and no build tools** — only CI pipeline configuration files:

- `.circleci/config.yml` — CircleCI pipeline (echo commands)
- `.travis.yml` — Travis CI config (echo commands)
- `.gitlab-ci.yml` — GitLab CI config (echo commands in build/test stages)

### Lint / Test / Build / Run

- **Lint**: Validate YAML syntax with `python3 -c "import yaml; yaml.safe_load(open('<file>'))"` for each CI config file.
- **Test**: No automated tests exist. CI scripts only contain `echo` commands; run them locally in a shell to verify.
- **Build**: No build step required.
- **Run**: No application to run. To simulate CI jobs locally, execute the `echo` commands from each config file.

### Notes

- There are no dependencies to install and no package managers in use.
- All CI configs are YAML; changes should be validated for correct YAML syntax before committing.
