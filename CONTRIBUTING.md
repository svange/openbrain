# Contributing to OpenBrain

## ADD
notes and scripts for commitizen 

Thank you for your interest in contributing to OpenBrain! This guide will help you set up your development environment and walk you through our contribution workflow.

## Prerequisites

1. **Python 3.11**: This project requires Python 3.11, which you can download from [here](https://www.python.org/downloads/).
  
2. **Poetry**: We use Poetry for dependency management. Install it from [Poetry's official website](https://python-poetry.org/docs/#installation), **not from pip**.

3. **Pre-commit**: This project uses pre-commit hooks. Install it using:
    ```
    pre-commit install
    ```
   
4. Commitizen: This project uses Commitizen to enforce the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard. Commit messages can be generated using:
    ```
    cz commit
    ```

4. **AWS Credentials**: Ensure you have AWS credentials configured for testing.

## Setting Up the Development Environment

1. **Fork the Repository**: Fork this repository to your own GitHub account.

1. **Clone Your Fork Locally**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Project_Name.git
    ```

1. **Navigate to the Project Directory**:
    ```bash
    cd Project_Name
    ```
   
1. **Set up Environment Variables**: Copy the `.env.example` to `.env` and populate it with the necessary variables.

2. **Deploy AWS Supporting Infrastructure Stack**:
    ```bash
    poetry run python ci_cd.py -I
    ```

1. **Install Dependencies Using Poetry**:
    ```bash
    poetry install
    ```

1. **Activate the Poetry Environment**:
    ```bash
    poetry shell
    ```

1. **Install Pre-commit Hooks**:
    ```bash
    pre-commit install
    ```

1. **(Optional) Update Dependencies**: If you add or update dependencies, make sure to update `poetry.lock`:
    ```bash
    poetry update
    ```

1. **Run Tests to Verify Setup**:
    ```bash
    poetry run pytest
    ```

## Contributing Workflow

1. **Sync Your Fork**: Make sure your fork is up-to-date with the upstream repository:
    ```bash
    git remote add upstream https://github.com/ORIGINAL_OWNER/ORIGINAL_REPOSITORY.git
    git fetch upstream
    git merge upstream/main
    ```

2. **Create a New Branch**: Use `feat/<name>` for features and `fix/<name>` for bug fixes.
    ```bash
    git checkout -b feat/new-feature
    ```

3. **Make Your Changes**: Write your code, adhering to the current coding standards.

4. **Run Tests**:
    ```bash
    poetry run pytest
    ```

5. **Run Pre-commit Checks**:
    ```bash
    pre-commit run --all-files
    ```

6. **Commit Your Changes**: 
    ```bash
    git add .
    git commit -m "Describe your changes"
    ```

7. **Push to Your Fork**:
    ```bash
    git push origin feat/new-feature
    ```

8. **Create a Pull Request (PR)**: Navigate to your fork on GitHub and click on "New Pull Request."

### Notes on PRs and Dependencies

- PRs will be rejected if they do not pass all tests and pre-commit checks.
- If you added or updated dependencies, make sure to include the updated `poetry.lock` file in your PR.

---

Feel free to edit this guide as you see fit. It's designed to provide a comprehensive outline for potential contributors.