# src/ycurl/cli.py
"""Command‑line interface for ycurl (Typer version)."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from .executor import EndpointExecutor
from .registry import Registry
from .scaffold import create_app_structure

console = Console()
app = typer.Typer(add_completion=False, no_args_is_help=True)

# --------------------------------------------------------------------------- #
# Shared option objects (keeps Ruff happy about B008)                         #
# --------------------------------------------------------------------------- #
ENV_OPT = typer.Option(None, "--env", help="Environment to use (dev, prod …)")
CURLIFY_OPT = typer.Option(False, "--curlify", help="Show equivalent curl command")
OUTPUT_OPT = typer.Option(
    None, "--output", exists=False, help="Write response body to file"
)
QUIET_OPT = typer.Option(False, "--quiet", help="Suppress logs (except body)")
ONLY_STATUS_OPT = typer.Option(False, "--only-status", help="Show only HTTP status")

INIT_PATH_OPT = typer.Option(
    Path("."),
    "--path",
    file_okay=False,
    dir_okay=True,
    writable=True,
    help="Where to create the app",
)


# --------------------------------------------------------------------------- #
@app.callback(invoke_without_command=True)  # type: ignore[misc]
def main_callback(
    ctx: typer.Context,
    endpoint: str | None = typer.Argument(None, help="Endpoint name to run"),
    env: str | None = ENV_OPT,
    curlify: bool = CURLIFY_OPT,
    output_path: Path | None = OUTPUT_OPT,
    quiet: bool = QUIET_OPT,
    only_status: bool = ONLY_STATUS_OPT,
) -> None:
    """Run an endpoint or dispatch to a sub‑command."""
    if ctx.invoked_subcommand is not None:
        return

    if endpoint is None:
        console.print("[red]Error:[/] No endpoint specified.", highlight=False)
        raise typer.Exit(1)

    # mypy now knows endpoint is str
    _run_endpoint(
        endpoint,
        env=env,
        curlify=curlify,
        output_path=output_path,
        quiet=quiet,
        only_status=only_status,
    )


# --------------------------------------------------------------------------- #
@app.command("init")  # type: ignore[misc]
def init(
    app_name: str = typer.Argument(..., help="Name of the new ycurl app"),
    path: Path = INIT_PATH_OPT,
) -> None:
    """Create a new ycurl application scaffold."""
    app_dir = create_app_structure(app_name, path)
    console.print(f"[green]✔ App created:[/] {app_dir}")


@app.command("list-local")  # type: ignore[misc]
def list_local() -> None:
    """List all registered ycurl apps on this machine."""
    for entry in Registry().all():
        console.print(f"[bold]{entry.name}[/] → {entry.path}")


@app.command("complete")  # type: ignore[misc]
def complete(shell: str = typer.Argument(..., help="bash | zsh")) -> None:
    """Emit a one‑liner for shell completion."""
    if shell not in {"bash", "zsh"}:
        console.print("Supported shells: bash, zsh", style="red")
        raise typer.Exit(1)
    cmd = f"_YCURL_COMPLETE={shell}_source ycurl"
    console.print(cmd)


# --------------------------------------------------------------------------- #
def _run_endpoint(
    endpoint_name: str,
    *,
    env: str | None,
    curlify: bool,
    output_path: Path | None,
    quiet: bool,
    only_status: bool,
) -> None:
    """Prepare, execute, and print an endpoint request/response."""
    executor = EndpointExecutor(
        endpoint_name,
        env=env,
        curlify=curlify,
        dry_run=False,
    )

    prepared = executor.prepare()

    if curlify:
        console.print(prepared.as_curl())
        sys.exit(0)

    response = executor.execute()

    if only_status:
        console.print(str(response.status_code))
        sys.exit(0)

    if not quiet:
        console.print(
            f"[bold]{response.status_code}[/] {response.reason_phrase} "
            f"({response.elapsed.total_seconds():.2f}s)"
        )

    console.print(response.pretty_body())

    if output_path:
        output_path.write_text(response.body, encoding="utf-8")
        console.print(f"[dim]Body written to {output_path}[/]")


if __name__ == "__main__":
    app()
