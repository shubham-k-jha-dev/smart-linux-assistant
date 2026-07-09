"""
Command-line interface for the Smart Linux Assistant.
"""

from __future__ import annotations
import sys
import typer
from linux_assistant.exceptions import CommandExecutionError, CommandFailedError, CommandTimeoutError, ValidationError, MissingAPIKeyError, ServiceError, RateLimitError
from linux_assistant.services.explainer import Explainer
from linux_assistant.services.command_executor import CommandExecutor
from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.shell import command_exists
from linux_assistant.services.search import Searcher

logger = get_logger(__name__)

app = typer.Typer(
    name="smart-linux",
    help="An AI-powered Linux productivity assistant.",
    add_completion=False,
)

@app.callback()
def callback() -> None:
    """
    Smart Linux Assistant — an AI-powered Linux productivity CLI.
    """

@app.command()
def run(
    command: str = typer.Argument(..., help="The shell command to execute."),
    timeout: int = typer.Option(30, help="Timeout in seconds."),
    check: bool = typer.Option(
        False, "--check", help="Exit non-zero if the command itself fails."
    ),
) -> None:
    """
    Execute a shell command and display structured results.
    """
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
        raise typer.Exit(code=exc.result.exit_code)

    except CommandExecutionError as exc:
        typer.secho(f"Execution error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

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
    try:
        explainer = Explainer()
        result = explainer.explain(text)

    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    except ValidationError as exc:
        typer.secho(f"Invalid input: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    
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
    try:
        searcher = Searcher()
        result = searcher.search(query)

    except MissingAPIKeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    except ValidationError as exc:
        typer.secho(f"Invalid input: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    
    except RateLimitError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)

    except ServiceError as exc:
        typer.secho(f"Search failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.echo(result)


def main() -> None:
    """Entry point wrapper, used by the packaged console script."""
    app()


if __name__ == "__main__":
    main()