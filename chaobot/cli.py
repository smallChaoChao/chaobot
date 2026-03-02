"""CLI commands for chaobot using typer."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from chaobot import __version__

app = typer.Typer(
    name="chaobot",
    help="🤖 chaobot: A lightweight personal AI assistant",
    no_args_is_help=True,
)
console = Console()

LOGO = "🤖"


def version_callback(value: bool) -> None:
    if value:
        console.print(f"{LOGO} chaobot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """🤖 chaobot: A lightweight personal AI assistant."""
    pass


@app.command()
def init() -> None:
    """Initialize config & workspace."""
    from chaobot.config.manager import ConfigManager
    from chaobot.agent.memory import MemoryManager

    config_manager = ConfigManager()
    config_manager.initialize()

    config = config_manager.load()
    MemoryManager(config)

    console.print(Panel.fit(
        "✅ chaobot initialized successfully!\n\n"
        "Directory structure:\n"
        "  ~/.chaobot/config.json\n"
        "  ~/.chaobot/workspace/memory/MEMORY.md\n"
        "  ~/.chaobot/workspace/sessions/\n\n"
        "Next steps:\n"
        "1. Edit ~/.chaobot/config.json to add your API keys\n"
        "2. Run 'chaobot run' to start chatting",
        title=f"{LOGO} chaobot",
        border_style="green"
    ))


@app.command()
def run(
    message: Optional[str] = typer.Argument(
        None,
        help="Message to send (if not provided, starts interactive mode)",
    ),
    no_markdown: bool = typer.Option(
        False,
        "--no-markdown",
        help="Show plain-text replies",
    ),
    logs: bool = typer.Option(
        False,
        "--logs",
        "-l",
        help="Show runtime logs during chat",
    ),
    no_stream: bool = typer.Option(
        False,
        "--no-stream",
        help="Disable streaming response",
    ),
    session: str = typer.Option(
        "default",
        "--session",
        "-s",
        help="Session ID for conversation history",
    ),
) -> None:
    """Chat with the agent.

    Examples:
        chaobot run                    # Interactive mode
        chaobot run "Hello"            # Single message
        chaobot run -l "Hello"         # With logs
        chaobot run -s mysession       # Use specific session
    """
    from chaobot.agent.runner import AgentRunner

    runner = AgentRunner(
        show_logs=logs,
        use_markdown=not no_markdown,
        stream=not no_stream,
        session_id=session
    )

    if message:
        runner.run_single(message)
    else:
        runner.run_interactive()


@app.command()
def server() -> None:
    """Start the server (connects to enabled channels)."""
    from chaobot.gateway.server import GatewayServer

    gateway = GatewayServer()
    gateway.start()


@app.command()
def status() -> None:
    """Show status."""
    from chaobot.config.manager import ConfigManager
    from chaobot.providers.registry import ProviderRegistry

    config = ConfigManager().load()
    registry = ProviderRegistry()
    active_providers = registry.get_active_providers(config)

    table = Table(title=f"{LOGO} chaobot Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Config", str(config.config_path))
    table.add_row("Workspace", str(config.workspace_path))
    table.add_row("Active Providers", str(len(active_providers)))
    table.add_row("Model", config.agents.defaults.model)

    console.print(table)


@app.command()
def config(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser"),
) -> None:
    """Launch dashboard-based configuration UI."""
    import webbrowser
    from chaobot.dashboard.app import create_app

    app_flask = create_app()
    url = f"http://{host}:{port}"

    console.print(Panel.fit(
        f"🌐 Configuration UI starting...\n\n"
        f"URL: {url}\n\n"
        f"Use this web interface to:\n"
        f"  • Switch between AI models\n"
        f"  • Configure API keys\n"
        f"  • Set up message channels\n"
        f"  • Edit raw JSON config\n\n"
        f"Press Ctrl+C to stop",
        title=f"{LOGO} chaobot Config",
        border_style="green"
    ))

    if not no_browser:
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    app_flask.run(host=host, port=port, debug=False)


session_app = typer.Typer(name="session", help="Manage conversation sessions")
app.add_typer(session_app, name="session")


@session_app.callback(invoke_without_command=True)
def session_main(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(5000, "--port", "-p"),
    ctx: typer.Context = typer.Context,
) -> None:
    """Manage conversation sessions.

    Without subcommand: Start web UI for session management.
    """
    if ctx.invoked_subcommand is None:
        try:
            from chaobot.dashboard.session_manager import run_manager
            run_manager(host=host, port=port)
        except ImportError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Please install required dependencies:[/yellow]")
            console.print("  pip install flask")
            raise typer.Exit(1)


@session_app.command(name="list")
def session_list() -> None:
    """List all conversation sessions."""
    from chaobot.config.manager import ConfigManager
    from chaobot.agent.memory import MemoryManager

    config = ConfigManager().load()
    memory = MemoryManager(config)
    sessions = memory.get_all_sessions()

    if not sessions:
        console.print("No sessions found")
        return

    table = Table(title="📝 Sessions")
    table.add_column("Session ID", style="cyan")

    for s in sorted(sessions):
        table.add_row(s)

    console.print(table)


@session_app.command(name="clear")
def session_clear(
    session_id: Optional[str] = typer.Argument(None, help="Session ID to clear"),
    clear_all: bool = typer.Option(False, "--all", "-a", help="Clear all sessions"),
) -> None:
    """Clear conversation history for a session.

    Examples:
        chaobot session clear              # Clear default session
        chaobot session clear mysession    # Clear specific session
        chaobot session clear --all        # Clear all sessions
    """
    from chaobot.config.manager import ConfigManager
    from chaobot.agent.memory import MemoryManager

    config = ConfigManager().load()
    memory = MemoryManager(config)

    if clear_all:
        sessions = memory.get_all_sessions()
        for sid in sessions:
            asyncio.run(memory.clear_history(sid))
        console.print(f"✅ Cleared {len(sessions)} session(s)")
    else:
        sid = session_id or "default"
        asyncio.run(memory.clear_history(sid))
        console.print(f"✅ Cleared session: {sid}")


@session_app.command(name="ui")
def session_ui(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(5000, "--port", "-p"),
) -> None:
    """Start web interface for session management."""
    try:
        from chaobot.dashboard.session_manager import run_manager
        run_manager(host=host, port=port)
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please install required dependencies:[/yellow]")
        console.print("  pip install flask")
        raise typer.Exit(1)


cron_app = typer.Typer(name="cron", help="Manage scheduled tasks")
app.add_typer(cron_app, name="cron")


@cron_app.command(name="add")
def cron_add(
    name: str = typer.Option(..., "--name", "-n", help="Task name"),
    message: str = typer.Option(..., "--message", "-m", help="Message to send"),
    cron: Optional[str] = typer.Option(None, "--cron", "-c", help="Cron expression"),
    every: Optional[int] = typer.Option(None, "--every", "-e", help="Run every N seconds"),
) -> None:
    """Add a scheduled task."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    if cron:
        manager.add_cron(name, message, cron)
    elif every:
        manager.add_interval(name, message, every)
    else:
        console.print("[red]Either --cron or --every must be specified[/red]")
        raise typer.Exit(1)

    console.print(f"✅ Added task: {name}")


@cron_app.command(name="list")
def cron_list() -> None:
    """List scheduled tasks."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    tasks = manager.list_tasks()

    if not tasks:
        console.print("No scheduled tasks")
        return

    table = Table(title="⏰ Scheduled Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Schedule", style="yellow")

    for task in tasks:
        table.add_row(str(task.id), task.name, task.schedule)

    console.print(table)


@cron_app.command(name="remove")
def cron_remove(
    task_id: str = typer.Argument(..., help="Task ID to remove"),
) -> None:
    """Remove a scheduled task."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    manager.remove_task(task_id)
    console.print(f"✅ Removed task: {task_id}")


if __name__ == "__main__":
    app()
