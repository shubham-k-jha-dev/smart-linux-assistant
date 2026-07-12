"""
Command-line interface for the Smart Linux Assistant.
"""

from __future__ import annotations
import os
import sys
import typer
from linux_assistant.exceptions import CommandExecutionError, CommandFailedError, CommandTimeoutError, HistoryError, ValidationError, MissingAPIKeyError, ServiceError, RateLimitError
from linux_assistant.services.explainer import Explainer
from linux_assistant.services.command_executor import CommandExecutor
from linux_assistant.repositories import HistoryRepository
from linux_assistant.utils.logger import get_logger, set_verbose
from linux_assistant.utils.shell import command_exists
from linux_assistant.services.search import Searcher
from linux_assistant.models.history_entry import HistoryEntry

logger = get_logger(__name__)

HISTORY_OPT_OUT = "SMART_LINUX_NO_HISTORY"


def _record_history(
    *, command: str, exit_code: int, duration_seconds: float, stderr: str
) -> None:
    """
    Record a completed command invocation to the history store, as a
    best-effort side-effect. Respects SMART_LINUX_NO_HISTORY as an
    opt-out. Any failure to record is logged and silently swallowed —
    a broken history store must never interrupt the command the user
    actually asked to run.
    """
    if os.environ.get(HISTORY_OPT_OUT) == "1":
        return

    try:
        HistoryRepository().record(
            command=command,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
            working_directory=os.getcwd(),
            stderr=stderr,
        )
    except HistoryError as exc:
        logger.warning(f"Could not record command history: {exc}")

app = typer.Typer(
    name="smart-linux",
    help="An AI-powered Linux productivity assistant.",
    add_completion=False,
)

@app.callback()
def callback(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed internal logs on the console."
    ),
) -> None:
    """
    Smart Linux Assistant — an AI-powered Linux productivity CLI.
    """
    set_verbose(verbose)

@app.command()
def run(
    command: str = typer.Argument(..., help="The shell command to execute."),
    timeout: int = typer.Option(30, help="Timeout in seconds."),
    check: bool = typer.Option(
        False, "--check", help="Exit non-zero if the command itself fails."
    ),
    suggest_fix: bool = typer.Option(
        False, "--suggest-fix", help="If the command fails, suggest an AI-generated fix."
    ),
) -> None:
    """
    Execute a shell command and display structured results.
    """
    
    if suggest_fix and not check:
        typer.secho(
            "Invalid usage: --suggest-fix requires --check (fix suggestions only apply to command failures detected via --check).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    executor = CommandExecutor()
    
    try:
        if check:
            result = executor.execute_checked(command, timeout=timeout)
        else:
            result = executor.execute(command, timeout=timeout)

    except ValidationError as exc:
        typer.secho(f"Invalid input: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    except CommandTimeoutError as exc:
        typer.secho(f"Timed out: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=124)

    except CommandFailedError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        if exc.result.stderr:
            typer.secho(exc.result.stderr, fg=typer.colors.YELLOW, err=True)

        _record_history(
            command=command,
            exit_code=exc.result.exit_code,
            duration_seconds=exc.result.duration_seconds,
            stderr=exc.result.stderr,
        )

        if suggest_fix:
            typer.echo()
            try:
                explainer = Explainer()
                suggestion = explainer.suggest_fix(command, exc.result.stderr)

            except MissingAPIKeyError as fix_exc:
                typer.secho(str(fix_exc), fg=typer.colors.RED, err=True)

            except RateLimitError as fix_exc:
                typer.secho(str(fix_exc), fg=typer.colors.YELLOW, err=True)

            except ServiceError as fix_exc:
                typer.secho(f"Could not get a fix suggestion: {fix_exc}", fg=typer.colors.RED, err=True)

            else:
                if suggestion is None:
                    typer.secho("No confident fix available.", fg=typer.colors.YELLOW)
                else:
                    typer.secho("Suggested fix:", fg=typer.colors.CYAN)
                    typer.echo(f"  {suggestion}")

        raise typer.Exit(code=exc.result.exit_code)

    except CommandExecutionError as exc:
        typer.secho(f"Execution error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    _record_history(
        command=command,
        exit_code=result.exit_code,
        duration_seconds=result.duration_seconds,
        stderr=result.stderr,
    )

    if result.stdout:
        typer.echo(result.stdout)
    if result.stderr:
        typer.secho(result.stderr, fg=typer.colors.YELLOW, err=True)

    raise typer.Exit(code=result.exit_code)

DOCTOR_CHECKS: tuple[str, ...] = (
    "bash",
    "git",
    "python3",
    "docker",
    "curl",
    "systemctl",
)


@app.command()
def doctor() -> None:
    """
    Check for the presence of common tools on this system.
    """
    typer.echo("Running environment checks...\n")

    missing: list[str] = []

    for tool in DOCTOR_CHECKS:
        exists = command_exists(tool)
        symbol = "✔" if exists else "✘"
        color = typer.colors.GREEN if exists else typer.colors.RED
        typer.secho(f"  {symbol}  {tool}", fg=color)

        if not exists:
            missing.append(tool)

    typer.echo()

    if missing:
        typer.secho(
            f"{len(missing)} tool(s) missing: {', '.join(missing)}",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)

    typer.secho("All checked tools are available.", fg=typer.colors.GREEN)
    
@app.command()
def explain(
    text: str = typer.Argument(
        ..., help="The command, error message, or output to explain."
    ),
) -> None:
    """
    Get a plain-language explanation of a command or error message.
    """
    if not text.strip():
        typer.secho("Invalid input: Text to explain cannot be empty.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    
    try:
        explainer = Explainer()
        result = explainer.explain(text)

    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
   
    except RateLimitError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    except ServiceError as exc:
        typer.secho(f"Explanation failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.echo(result)
    
@app.command()
def fix(
    command: str = typer.Argument(..., help="The failing command to fix."),
    timeout: int = typer.Option(30, help="Timeout in seconds."),
) -> None:
    """
    Run a command, and if it fails, suggest a corrected version.
    """
    executor = CommandExecutor()

    try:
        result = executor.execute(command, timeout=timeout)

    except ValidationError as exc:
        typer.secho(f"Invalid input: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    
    except CommandTimeoutError as exc:
        typer.secho(f"Timed out: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=124)

    except CommandExecutionError as exc:
        typer.secho(f"Execution error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if result.succeeded:
        typer.secho(f"Command succeeded, nothing to fix.", fg=typer.colors.GREEN)
        if result.stdout:
            typer.echo(result.stdout)
        raise typer.Exit(code=0)

    typer.secho(f"Command failed: {result.stderr or '(no error output)'}", fg=typer.colors.RED)
    typer.echo()
   
    try:
        explainer = Explainer()
        suggestion = explainer.suggest_fix(command, result.stderr)

    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    
    except RateLimitError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    except ServiceError as exc:
        typer.secho(f"Could not get a fix suggestion: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if suggestion is None:
        typer.secho("No confident fix available.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    typer.secho("Suggested fix:", fg=typer.colors.CYAN)
    typer.echo(f"  {suggestion}")
    typer.echo()
    typer.echo(f'Run it manually, or try: smart-linux run "{suggestion}"')

    raise typer.Exit(code=1)

@app.command()
def search(
    query: str = typer.Argument(
        ..., help="A natural-language question about a Linux task."
    ),
) -> None:
    """
    Search for how to accomplish a Linux task in plain language.
    """
    if not query.strip():
        typer.secho("Invalid input: Search query cannot be empty.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    try:
        searcher = Searcher()
        result = searcher.search(query)

    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    except RateLimitError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    except ServiceError as exc:
        typer.secho(f"Search failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.echo(result)


history_app = typer.Typer(help="View and manage recorded command history.")
app.add_typer(history_app, name="history")


def _format_history_entry(entry) -> str:
    """
    Render a single HistoryEntry as a compact, human-readable line,
    with a failed entry's stderr snippet shown indented beneath it.
    """
    symbol = "✔" if entry.succeeded else "✘"
    timestamp = entry.executed_at.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp}  {symbol}  {entry.duration_seconds:.2f}s  {entry.command}"

    if entry.failed and entry.stderr_snippet:
        line += f"\n    └─ {entry.stderr_snippet}"

    return line


@history_app.callback(invoke_without_command=True)
def history_default(
    ctx: typer.Context,
    failures_only: bool = typer.Option(
        False, "--failures-only", help="Show only failed commands."
    ),
    limit: int = typer.Option(20, help="Maximum number of entries to show."),
) -> None:
    """
    Show recent command history. Defaults to listing; use 'clear' to
    wipe all recorded history.
    """
    if ctx.invoked_subcommand is not None:
        return

    try:
        entries = HistoryRepository().list_recent(limit=limit, failures_only=failures_only)
    except HistoryError as exc:
        typer.secho(f"Could not read history: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if not entries:
        typer.echo("No history recorded yet.")
        raise typer.Exit(code=0)

    for entry in entries:
        color = typer.colors.GREEN if entry.succeeded else typer.colors.RED
        typer.secho(_format_history_entry(entry), fg=color)


@history_app.command("clear")
def history_clear() -> None:
    """
    Permanently delete all recorded command history.
    """
    try:
        HistoryRepository().clear()
    except HistoryError as exc:
        typer.secho(f"Could not clear history: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho("Command history cleared.", fg=typer.colors.GREEN)


def main() -> None:
    """Entry point wrapper, used by the packaged console script."""
    app()


if __name__ == "__main__":
    main()