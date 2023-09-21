# Git Branching Strategy
Work in the following branches:
- `main` is protected and requires a pull request to merge.
- `dev` is the development branch and is deployed to the dev stage. Tagged changes to `dev` run tests, deploy to pypi-test, and submit a pull request to `main`.
- `prototype/<UNIQUE_NAME>` is used for local prototyping and is not deployed.
- `feature/<UNIQUE_NAME>` once stable, this prefix is used for feature development and is merged into `dev` for testing.
- `bugfix/<UNIQUE_NAME>` once stable, this prefix is used for bugfixes and is merged into `dev` for testing.

This repo uses Github Actions. See `.github/workflows` for the workflow definitions.