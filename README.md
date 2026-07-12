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

By default, the CLI stays quiet — internal logs are written only to the log file, not the console. Pass `--verbose` (or `-v`) before any subcommand to see detailed logs live in your terminal:

```bash
smart-linux --verbose run "echo hello"
```

- Run a shell command:

```bash
smart-linux run "echo hello"
```

- Options:
  - `--timeout <seconds>` — maximum seconds to allow command to run (default: 30)
  - `--check` — treat non-zero exit codes as errors and exit with that code
  - `--suggest-fix` — if the command fails, use AI to suggest a corrected version (requires `--check`; requires `GROQ_API_KEY`, same as `explain`/`fix`/`search`)

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

- Fix a failing command:

```bash
smart-linux fix "ls /nonexistent"
```

- Options:
  - `--timeout <seconds>` — maximum seconds to allow the command to run (default: 30)

- This runs the command and, if it fails, uses the AI to suggest a corrected version. Requires the same `GROQ_API_KEY` environment variable as the `explain` command.

- Search for a Linux task in plain language:

```bash
smart-linux search "find the 10 largest files in the current directory"
```

- This returns a concrete command and brief explanation for the requested task. Requires the same `GROQ_API_KEY` environment variable as the `explain` command.

- View or manage recorded command history:

```bash
smart-linux history
smart-linux history --failures-only
smart-linux history clear
```

  Every `run` invocation (success or failure) is recorded locally in a SQLite database, storing the command text, exit code, duration, working directory, and — only for failed commands — a truncated snippet of stderr. `stdout` is never stored. History is capped at 5,000 entries (oldest entries are pruned automatically) and can be disabled entirely by setting `SMART_LINUX_NO_HISTORY=1`.

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

Failed command with an AI-suggested fix:

```bash
$ smart-linux run "gti status" --check --suggest-fix
gti: command not found

Suggested fix:
  git status
```

`--suggest-fix` requires `--check` (fix suggestions only apply to command failures detected via `--check`); calling it without `--check` exits immediately with an error.

## Roadmap / Current Status

- Core CLI: implemented — `run` and `doctor` commands are provided in `linux_assistant.cli.main`.
- Command execution: implemented using `linux_assistant.services.command_executor.CommandExecutor` which returns `CommandResult` instances.
- Logging & configuration: implemented via `linux_assistant.utils.logger` and `linux_assistant.config.settings`.
- Packaging: console script entry points are declared in `pyproject.toml`.
- AI-powered explanations: implemented — `smart-linux explain` uses the Groq API (`llama-3.3-70b-versatile`) to generate plain-language explanations of commands and error messages, via `linux_assistant.services.explainer.Explainer`. Requires a user-supplied `GROQ_API_KEY` environment variable.
- AI-powered fix suggestions: implemented — `smart-linux fix` runs a failing command and suggests a corrected version; `smart-linux run --check --suggest-fix` offers the same suggestion inline as part of normal command execution. Both use `linux_assistant.services.explainer.Explainer.suggest_fix()`.
- AI-powered search: implemented — `smart-linux search` answers natural-language questions about Linux tasks via `linux_assistant.services.search.Searcher`.
- Production hardening: implemented — API timeouts, retry logic, rate-limit-specific handling, input truncation, and documented OS/privacy limitations across all AI-backed commands.
- Command history: implemented — `smart-linux run` records every invocation locally via `linux_assistant.repositories.history_repository.HistoryRepository` (SQLite-backed, FIFO-capped at 5,000 rows). View with `smart-linux history` (supports `--failures-only`), erase with `smart-linux history clear`, or disable entirely via `SMART_LINUX_NO_HISTORY=1`. AI-powered use of this history (e.g. `explain`/`fix` referencing past failures) is planned for a future version but not yet implemented.
- Additional AI features (documentation lookup) are planned but not yet implemented.

## Known Limitations

- Tested and verified on Linux (native and WSL). Not yet tested on macOS or native Windows Python — behavior on those platforms is currently unverified, though the codebase avoids Linux-only APIs where possible.

## Privacy Note

The `explain`, `fix`, and `search` commands send the command text, error output, or your query to Groq's API for processing. Avoid running these commands on text that contains secrets, passwords, or sensitive data, since that content leaves your machine.

Separately, `smart-linux run` records a local history of command invocations (command text, exit code, duration, working directory, and — for failures only — a truncated stderr snippet) in a SQLite database on your machine. This data never leaves your machine and is not sent to any API. `stdout` is never recorded. To disable history recording entirely, set `SMART_LINUX_NO_HISTORY=1`. To view or erase recorded history, use `smart-linux history` and `smart-linux history clear`.

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
