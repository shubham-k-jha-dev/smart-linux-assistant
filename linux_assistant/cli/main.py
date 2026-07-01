"""
Command-line interface for the Smart Linux Assistant.
"""

from __future__ import annotations
import sys
import typer
from linux_assistant.exceptions import CommandExecutionError, CommandFailedError, CommandTimeoutError, ValidationError
from linux_assistant.services.command_executor import CommandExecutor
from linux_assistant.utils.logger import get_logger
from linux_assistant.utils.shell import command_exists

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


def main() -> None:
    """Entry point wrapper, used by the packaged console script."""
    app()


if __name__ == "__main__":
    main()