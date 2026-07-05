# Smart Linux Assistant

Smart Linux Assistant is an AI-powered Linux operations assistant that understands natural language, safely executes shell commands, retrieves Linux knowledge, explains errors, and assists users with troubleshooting. The current version implements the core command execution engine and foundational architecture for future AI capabilities.

![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
[![CI](https://github.com/shubham-k-jha-dev/smart-linux-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/shubham-k-jha-dev/smart-linux-assistant/actions/workflows/ci.yml)

## Project Overview

Smart Linux Assistant is a command-line utility that executes shell commands and returns structured outcomes. The tool captures the command, exit code, stdout, stderr, execution timestamp, and duration to make downstream automation and logging straightforward.

## System Architecture

- CLI (`linux_assistant.cli.main`) accepts user commands and options and delegates execution to `CommandExecutor`.
- `CommandExecutor` runs shell commands using `subprocess.run` and returns a `CommandResult` dataclass describing the outcome.
- Centralized logging is provided by `linux_assistant.utils.logger`, writing to `logs/smart_linux_assistant.log` with rotation.
- Runtime paths and directories are managed by `linux_assistant.config.settings` and can be initialized with `initialize_app_filesystem()`.

## Tech Stack

- Python 3.11+
- Typer (CLI)
- Standard library: `subprocess`, `logging`, `shutil`, `dataclasses`, `pathlib`, `datetime`

## Prerequisites

1. Python 3.11 or newer.
2. Optional: a virtual environment tool (`venv`).
3. No Dockerfile or docker-compose are included in this repository.

## Local Setup & Installation

1. Clone the repository:

```bash
git clone https://github.com/shubham-k-jha-dev/smart-linux-assistant
cd smart-linux-assistant
```

2. Create and activate a virtual environment:

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

3. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

4. (Optional) Install the package in editable mode to enable the `smart-linux` CLI entrypoint:

```bash
pip install -e .
```

5. (Optional) Ensure runtime directories exist from Python:

```python
from linux_assistant.config.settings import initialize_app_filesystem
initialize_app_filesystem()
```

## Environment Variables

This project does not require any environment variables for its core CLI functionality. The repository includes an empty `.env.example` placeholder.

| Variable | Description | Example |
|----------|-------------|---------|
| (none) | No required environment variables for CLI execution | - |

## Usage / API Reference

The project exposes the console scripts `smart-linux` and `sla` (configured in `pyproject.toml`).

- Run a shell command:

```bash
smart-linux run "echo hello"
```

- Options:
  - `--timeout <seconds>` — maximum seconds to allow command to run (default: 30)
  - `--check` — treat non-zero exit codes as errors and exit with that code

- Doctor command (checks common tools):

```bash
smart-linux doctor
```
- Get an AI-powered explanation of a command or error message:

```bash
smart-linux explain "permission denied when running ./script.sh"
```

  Requires a free Groq API key set as an environment variable:

```bash
export GROQ_API_KEY="your-key-here"
```

  Get a free key at [console.groq.com](https://console.groq.com).

### Example output

Successful command:

```bash
$ smart-linux run "echo hello"
hello
```

Failed command (example):

```bash
$ smart-linux run "ls nonexistent" --check
ls: cannot access 'nonexistent': No such file or directory
```

These outputs reflect the CLI behaviour: standard output is printed for successful commands; standard error is printed for failures and, when `--check` is used, the CLI exits with the command's exit code.

## Roadmap / Current Status

- Core CLI: implemented — `run` and `doctor` commands are provided in `linux_assistant.cli.main`.
- Command execution: implemented using `linux_assistant.services.command_executor.CommandExecutor` which returns `CommandResult` instances.
- Logging & configuration: implemented via `linux_assistant.utils.logger` and `linux_assistant.config.settings`.
- Packaging: console script entry points are declared in `pyproject.toml`.
- AI-powered explanations: implemented — `smart-linux explain` uses the Groq API (`llama-3.3-70b-versatile`) to generate plain-language explanations of commands and error messages, via `linux_assistant.services.explainer.Explainer`. Requires a user-supplied `GROQ_API_KEY` environment variable.
- Additional AI features (command suggestions, history analysis, documentation lookup) are planned but not yet implemented.

## Install from PyPI

If this package is published to PyPI, it can be installed with:

```bash
pip install smart-linux-assistant
```

## Testing

Run the test suite with `pytest`:

```bash
pytest
```

## License

MIT License — see `LICENSE`.

## Contributing

- Run tests with `pytest` before opening a pull request.
- Follow standard Python packaging best practices.
