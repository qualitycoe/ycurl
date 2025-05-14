"""Command‑line interface built with Click."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import ConfigLoader
from .constants import APP_MARKER
from .exceptions import EndpointNotFound
from .http_client import RequestExecutor
from .registry import Registry
from .utils import find_app_root, pretty_print_json

console = Console()


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.pass_context
@click.option("--env", "env", help="Environment to use (dev, prod, ...)")
@click.option("--dry-run", is_flag=True, help="Print request without sending")
@click.option("--curlify", is_flag=True, help="Print equivalent curl command")
@click.option(
    "--curlify-copy", is_flag=True, help="Print curl and copy to clipboard", hidden=True
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(writable=True),
    help="Write response body to file",
)
@click.option("--quiet", is_flag=True, help="Suppress logs, show only response body")
@click.option("--only-status", is_flag=True, help="Show only HTTP status code")
@click.argument("endpoint", required=False)
def cli(
    ctx: click.Context,
    env: str | None,
    dry_run: bool,
    curlify: bool,
    curlify_copy: bool,
    output_path: str | None,
    quiet: bool,
    only_status: bool,
    endpoint: str | None,
) -> None:
    """ycurl – run or manage shareable HTTP request recipes."""
    if ctx.invoked_subcommand is not None:
        # sub‑command like init, list-local
        return

    if endpoint is None:
        click.echo(ctx.get_help())
        return

    _run_endpoint(
        endpoint,
        env=env,
        dry_run=dry_run,
        curlify=curlify,
        output_path=output_path,
        quiet=quiet,
        only_status=only_status,
    )


# ==================================================
# Sub‑commands
# ==================================================


@cli.command("init")
@click.argument("app_name", type=str)
@click.option(
    "--path",
    "base_path",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="Directory to create the app in",
)
def init_app(app_name: str, base_path: str) -> None:
    """Initialise a new ycurl project."""
    base = Path(base_path).resolve()
    app_dir = base / app_name
    endpoints_dir = app_dir / "endpoints"
    app_dir.mkdir(parents=True, exist_ok=True)
    endpoints_dir.mkdir(exist_ok=True)

    (app_dir / APP_MARKER).touch()
    (app_dir / f"{app_name}.default.yaml").write_text(
        "# base config\nbase_url: \nheaders: {}\n", encoding="utf‑8"
    )
    Registry().add(app_name, app_dir)
    console.print(f"[green]Initialised ycurl app in {app_dir}")


@cli.command("list-local")
def list_local() -> None:
    """Show all registered ycurl apps."""
    reg = Registry()
    table = Table(title="Registered ycurl projects")
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("Created")

    for proj in reg.list_all():
        table.add_row(proj["name"], proj["path"], proj["created"])
    console.print(table)


@cli.command("complete")
@click.argument("shell", type=click.Choice(["bash", "zsh"]))
def complete(shell: str) -> None:
    """Generate shell completion snippet."""
    if shell == "bash":
        snippet = "_YCURL_COMPLETE=bash_source ycurl"
    else:
        snippet = "_YCURL_COMPLETE=zsh_source ycurl"
    console.print(snippet)


# ==================================================
# Internal execution helper
# ==================================================


def _run_endpoint(
    endpoint_name: str,
    *,
    env: str | None,
    dry_run: bool,
    curlify: bool,
    output_path: str | None,
    quiet: bool,
    only_status: bool,
) -> None:
    app_root = find_app_root()
    if app_root is None:
        raise click.ClickException("Not inside a ycurl app (missing .ycurl)")

    endpoint_file = app_root / "endpoints" / f"{endpoint_name}.yaml"
    if not endpoint_file.exists():
        raise EndpointNotFound(f"Endpoint YAML not found: {endpoint_file}")

    cfg_loader = ConfigLoader(env=env, app_root=app_root)
    resolved = cfg_loader.resolve(endpoint_file)
    merged = resolved.merged

    executor = RequestExecutor(merged)
    prepared = executor.prepare()

    # Handle meta‑flags
    if curlify or dry_run:
        console.print(prepared.as_curl())
        if dry_run:
            return

    if curlify:  # only curlify but still execute
        console.print()

    # Send the HTTP request
    resp = asyncio.run(executor.send(prepared))

    if only_status:
        console.print(resp.status_code)
        return

    if not quiet:
        console.print(
            f"[bold]{resp.status_code}[/] {resp.reason_phrase} – {resp.elapsed.total_seconds():.2f}s"
        )

    # Body printing / save to file
    body_bytes = resp.content
    if output_path:
        Path(output_path).write_bytes(body_bytes)
        if not quiet:
            console.print(f"[green]Body written to {output_path}")
    else:
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            pretty_print_json(body_bytes)
        else:
            console.print(body_bytes.decode(errors="replace"))
