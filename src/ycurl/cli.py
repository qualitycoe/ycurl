# src/ycurl/cli.py
"""Command‑line interface for ycurl (Typer version)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import typer
from rich.console import Console

from .executor import EndpointExecutor
from .registry import Registry
from .scaffold import create_app_structure
from .utils import curlify as cfy

console = Console()
app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
cli = app

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
DRY_RUN_OPT = typer.Option(
    False, "--dry-run", help="Show request details, send nothing"
)

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
    endpoint: str | None = typer.Argument(
        None,
        help="Endpoint name (default action) or sub-command",
    ),
    env: str | None = ENV_OPT,
    curlify: bool = CURLIFY_OPT,
    dry_run: bool = DRY_RUN_OPT,
    output_path: Path | None = OUTPUT_OPT,
    quiet: bool = QUIET_OPT,
    only_status: bool = ONLY_STATUS_OPT,
) -> None:
    """
    Root entry-point.

    * If *endpoint* matches a registered sub-command, forward to it.
    * Otherwise treat it as an endpoint name and run the request.
    """
    # -------------------------------------------------- #
    # 1) forward to real sub-commands when typo-less
    # -------------------------------------------------- #
    SUB_CMD_BY_NAME: dict[str, Callable[..., Any]] = {
        "init": init,
        "list-local": list_local,
        "complete": complete,
    }
    if endpoint in SUB_CMD_BY_NAME:
        ctx.invoke(SUB_CMD_BY_NAME[endpoint], *ctx.args)
        return

    # ----------------------------------------------------------------------------
    # 2) Manual parse of leftover CLI tokens so users can put flags after endpoint
    # ----------------------------------------------------------------------------
    tokens = list(ctx.args)  # copy; we'll pop() as we parse
    while tokens:
        tok = tokens.pop(0)
        if tok == "--env" and tokens:
            env = tokens.pop(0)
        elif tok == "--curlify":
            curlify = True
        elif tok == "--dry-run":
            dry_run = True
        elif tok == "--output" and tokens:
            output_path = Path(tokens.pop(0))
        elif tok == "--quiet":
            quiet = True
        elif tok == "--only-status":
            only_status = True
        else:
            console.print(f"[red]Unknown or misplaced option:[/] {tok}")
            raise typer.Exit(1)

    # -------------------------------------------------- #
    # 3) default behaviour: run an endpoint recipe
    # -------------------------------------------------- #
    if endpoint is None:
        console.print("[red]Error:[/] No endpoint specified.", highlight=False)
        raise typer.Exit(1)

    _run_endpoint(
        endpoint,
        env=env,
        curlify=curlify,
        dry_run=dry_run,
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
    dry_run: bool,
    output_path: Path | None,
    quiet: bool,
    only_status: bool,
) -> None:
    """Prepare, execute, and print an endpoint request/response."""
    executor = EndpointExecutor(
        endpoint_name,
        env=env,
        dry_run=dry_run,
    )

    prepared = executor.prepare()

    if curlify:
        console.print(cfy(prepared))
        raise typer.Exit(0)

    response = executor.execute()

    if only_status:
        console.print(str(response.status_code))
        raise typer.Exit(0)

    if not quiet:
        console.print(
            f"[bold]{response.status_code}[/] {response.reason_phrase} "
            f"({response.elapsed.total_seconds():.2f}s)"
        )

    response.pretty_body()

    if output_path:
        output_path.write_text(response.body, encoding="utf-8")
        console.print(f"[dim]Body written to {output_path}[/]")


if __name__ == "__main__":
    cli()
