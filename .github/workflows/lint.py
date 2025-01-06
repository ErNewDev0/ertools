name: Format Code

on:
  push:
    paths:
    - "**.py"
  workflow_dispatch:

jobs:
  Format_Code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python Environment
        uses: actions/setup-python@v4
        with:
          python-version: "3.10.x"
      - name: Install Formatting Tools
        run: pip install autopep8 autoflake isort black
      - name: Run autopep8 Formatter
        run: |
          autopep8 --verbose --in-place --recursive --aggressive *.py
      - name: Clean Imports
        run: |
          isort .
          autoflake --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports .
      - name: Apply Code Formatting
        run: |
          black .
          isort .
      - name: Auto Commit Changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
            commit_message: "Auto-format code"
            commit_options: "--no-verify"
            repository: .
            commit_user_name: "ErNewDev0"
            commit_user_email: "172886759+github-actions[bot]@users.noreply.github.com"
            commit_author: "ErNewDev0 <172886759+github-actions[bot]@users.noreply.github.com>"