# Smart Linux Assistant

Smart Linux Assistant is an AI-powered Linux operations assistant that understands natural language, safely executes shell commands, retrieves Linux knowledge, explains errors, and assists users with troubleshooting. The current version implements the core command execution engine and foundational architecture for future AI capabilities.


## Features

- Execute Linux commands safely
- AI-powered command explanations
- AI-assisted command repair
- Natural language Linux search
- Local Linux manual page lookup
- Command history with context-aware AI
- Built-in safety checks for destructive commands
- Configurable AI providers and runtime settings

## System Architecture

* CLI (`linux_assistant.cli.main`) accepts user commands and options and delegates execution to `CommandExecutor`.
* `CommandExecutor` runs shell commands using `subprocess.run` and returns a `CommandResult` dataclass describing the outcome.
* Centralized logging is provided by `linux_assistant.utils.logger`, writing to `logs/smart_linux_assistant.log` with rotation.
* Configuration management is handled by `linux_assistant.config` using typed Dataclasses (`AppConfig`), lazy loading (`get_config()`), and strict TOML validation.
* Runtime paths and directories are managed by `linux_assistant.config.settings` and can be initialized with `initialize_app_filesystem()`.

## Tech Stack

* Python 3.11+
* Typer (CLI)
* Standard library: `subprocess`, `logging`, `shutil`, `dataclasses`, `pathlib`, `datetime`
* SQLite (command history)

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

Most CLI functionality (`run`, `history`, `docs`, and `doctor`) works entirely locally and does not require any environment variables.

AI-powered commands require a free Groq API key.

| Variable | Description | Required For |
|----------|-------------|--------------|
| `GROQ_API_KEY` | Groq API key used for AI-powered features. | `explain`, `fix`, `search`, `run --suggest-fix` |
| `SMART_LINUX_NO_HISTORY` | Set to `1` to disable recording of future command history in the local SQLite database. | Optional |

## Configuration

Smart Linux Assistant supports a user configuration file. If no configuration file is present, the application automatically falls back to built-in defaults.

By default, the application looks for:

```text
~/.config/smart-linux-assistant/config.toml
```

Smart Linux Assistant follows the XDG Base Directory Specification. If `XDG_CONFIG_HOME` is set, the configuration file is read from:
`$XDG_CONFIG_HOME/smart-linux-assistant/config.toml`

Otherwise, the default location `~/.config/smart-linux-assistant/config.toml` is used.

A complete example configuration is available in the repository as:
```
config.toml.example
```
Copy it into your local configuration directory and modify only the values you want to customize.
Example:
```
mkdir -p ~/.config/smart-linux-assistant
cp config.toml.example ~/.config/smart-linux-assistant/config.toml
```
Example `config.toml` structure:

```toml
[ai]
provider = "groq"
model = "llama-3.3-70b-versatile"
timeout_seconds = 10.0
max_retries = 3

[history]
enabled = true
max_entries = 5000

[logging]
verbose = false

[privacy]
redaction_enabled = true

Current configurable options include:

- AI provider
- AI model
- API timeout
- Retry count
- Command history settings
- Logging verbosity
- Privacy (secret redaction)

## Usage / API Reference

The project exposes the console scripts `smart-linux` and `sla` (configured in `pyproject.toml`).

By default, the CLI stays quiet — internal logs are written only to the log file, not the console. Pass `--verbose` (or `-v`) before any subcommand to see detailed logs live in your terminal:

```bash
smart-linux --verbose run "echo hello"
```

* Run a shell command:

```bash
smart-linux run "echo hello"
```

* Options:
* `--timeout <seconds>` — maximum seconds to allow command to run (default: 30)
* `--check` — treat non-zero exit codes as errors and exit with that code
* `--suggest-fix` — if the command fails, use AI to suggest a corrected version (requires `--check`; requires `GROQ_API_KEY`, same as `explain`/`fix`/`search`)


* Doctor command (checks common tools):

```bash
smart-linux doctor
```

* Get an AI-powered explanation of a command or error message:

```bash
smart-linux explain "permission denied when running ./script.sh"
```

Requires a free Groq API key set as an environment variable:

```bash
export GROQ_API_KEY="your-key-here"
```

Get a free key at [console.groq.com](https://console.groq.com).

* Fix a failing command:

```bash
smart-linux fix "ls /nonexistent"
```

* Options:
* `--timeout <seconds>` — maximum seconds to allow the command to run (default: 30)


* This runs the command and, if it fails, uses the AI to suggest a corrected version, then **interactively prompts you to execute the fix safely**. Requires the same `GROQ_API_KEY` environment variable as the `explain` command.
* Search for a Linux task in plain language:

```bash
smart-linux search "find the 10 largest files in the current directory"
```

* View local Linux documentation:

```bash
smart-linux docs ls
```

Examples:

```bash
smart-linux docs grep
smart-linux docs chmod
smart-linux docs find
```

This command displays concise sections from your local Linux manual pages, including the NAME, SYNOPSIS, DESCRIPTION, OPTIONS, and EXAMPLES sections when available.

> Note:
> This command requires the `man` utility to be installed on your system.

* This returns a concrete command and brief explanation for the requested task, and **interactively prompts you to execute the command directly**. Requires the same `GROQ_API_KEY` environment variable as the `explain` command.
* View or manage recorded command history:

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

## Available Commands

| Command | Purpose |
|----------|---------|
| `run` | Execute shell commands |
| `doctor` | Verify system dependencies |
| `explain` | AI explanation of commands/errors |
| `fix` | AI-assisted command correction |
| `search` | Natural language → Linux command |
| `docs` | View local Linux manual pages |
| `history` | View and manage command history |

## Roadmap / Current Status

* Core CLI: implemented — `run` and `doctor` commands are provided in `linux_assistant.cli.main`.
* Command execution: implemented using `linux_assistant.services.command_executor.CommandExecutor` which returns `CommandResult` instances.
* Logging & typed configuration: implemented via `linux_assistant.utils.logger` and `linux_assistant.config` (featuring XDG compliance, strict TOML validation, dataclass schema mapping, and lazy cached loading via `lru_cache`).
* Packaging: console script entry points are declared in `pyproject.toml`.
* AI-powered explanations: implemented — `smart-linux explain` uses the Groq API (`llama-3.3-70b-versatile`) to generate plain-language explanations of commands and error messages, via `linux_assistant.services.explainer.Explainer`. Requires a user-supplied `GROQ_API_KEY` environment variable.
* AI-powered fix suggestions: implemented — `smart-linux fix` runs a failing command and suggests a corrected version; `smart-linux run --check --suggest-fix` offers the same suggestion inline as part of normal command execution. Both use `linux_assistant.services.explainer.Explainer.suggest_fix()`.
* AI-powered search: implemented — `smart-linux search` answers natural-language questions about Linux tasks via `linux_assistant.services.search.Searcher`.
* Production hardening & Safety: implemented — API timeouts, retry logic, rate-limit-specific handling, input truncation, regex-based secret redaction, and a **Heuristic Safety Interceptor (`linux_assistant.core.safety`)** to detect and block destructive commands (like `rm -rf`, `mkfs`, `dd`) before execution.
* Agentic Execution: implemented — `smart-linux fix` and `smart-linux search` now feature interactive confirmation prompts (`_prompt_and_execute`), allowing users to review AI-suggested commands and execute them instantly with safety guardrails.
* Command history: implemented — `smart-linux run` records every invocation locally via `linux_assistant.repositories.history_repository.HistoryRepository` (SQLite-backed, FIFO-capped at 5,000 rows). View with `smart-linux history` (supports `--failures-only`), erase with `smart-linux history clear`, or disable entirely via `SMART_LINUX_NO_HISTORY=1`. AI Context Injection is implemented: `explain` and `fix` commands dynamically fetch the last 5 chronological commands to give the LLM workflow awareness, protected by graceful degradation if the database is locked.
* Local documentation lookup: implemented — `smart-linux docs` retrieves Linux manual pages using the local `man` utility and extracts the most relevant sections (NAME, SYNOPSIS, DESCRIPTION, OPTIONS, and EXAMPLES) through `linux_assistant.services.documentation_service.DocumentationService`.

## Known Limitations

* Tested and verified on Linux (native and WSL). Not yet tested on macOS or native Windows Python — behavior on those platforms is currently unverified, though the codebase avoids Linux-only APIs where possible.
* The `docs` command depends on the `man` utility being available on the host system.

## Privacy Note

The `explain`, `fix`, and `search` commands send your terminal queries to Groq's API for processing. 

**Important update starting in v0.7.0+:** To provide context-aware solutions, the `fix` command securely reads your 5 most recent local commands and injects them into the Groq API prompt. 

**Security First:** Before any history leaves your machine, it passes through a local Regex Redactor (`linux_assistant.utils.redactor`) which automatically scrubs standard environment variables, inline passwords, AWS keys, and Bearer tokens, replacing them with `[REDACTED]`. However, you should still exercise caution and avoid running AI commands immediately after working with highly sensitive, non-standard plaintext secrets.

Separately, `smart-linux run` records your command invocations (command text, exit code, duration, working directory, and truncated stderr) in a local SQLite database. `stdout` is never recorded. To disable history recording entirely, set `SMART_LINUX_NO_HISTORY=1`. To view or erase recorded history, use `smart-linux history` and `smart-linux history clear`.

## Install from PyPI

If this package is published to PyPI, it can be installed with:

```bash
pip install smart-linux-assistant
```
Verify the installation:

```bash
smart-linux --help
```

## Testing

Run the test suite with `pytest`:

```bash
pytest
```

## License

MIT License — see `LICENSE`.

## Contributing

* Run tests with `pytest` before opening a pull request.
* Follow standard Python packaging best practices.