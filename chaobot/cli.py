"""CLI commands for chaobot."""

import click
from rich.console import Console
from rich.panel import Panel

from chaobot import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="chaobot")
def cli() -> None:
    """🤖 chaobot: A lightweight personal AI assistant."""
    pass


@cli.command()
def init() -> None:
    """Initialize config & workspace."""
    from chaobot.config.manager import ConfigManager
    from chaobot.agent.memory import MemoryManager

    config_manager = ConfigManager()
    config_manager.initialize()

    # Initialize memory system (creates MEMORY.md, HISTORY.md, and sessions dir)
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
        title="🤖 chaobot",
        border_style="green"
    ))


@cli.command()
@click.option("-m", "--message", help="Single message to send")
@click.option("--no-markdown", is_flag=True, help="Show plain-text replies")
@click.option("--logs", is_flag=True, help="Show runtime logs during chat")
@click.option("--no-stream", is_flag=True, help="Disable streaming response")
@click.option("--session", "-s", default="default", help="Session ID for conversation history")
def run(message: str | None, no_markdown: bool, logs: bool, no_stream: bool, session: str) -> None:
    """Chat with the agent."""
    from chaobot.agent.runner import AgentRunner

    runner = AgentRunner(show_logs=logs, use_markdown=not no_markdown, stream=not no_stream, session_id=session)

    if message:
        runner.run_single(message)
    else:
        runner.run_interactive()


@cli.command()
def server() -> None:
    """Start the server (connects to enabled channels)."""
    from chaobot.gateway.server import GatewayServer

    server = GatewayServer()
    server.start()


@cli.command()
def status() -> None:
    """Show status."""
    from chaobot.config.manager import ConfigManager
    from chaobot.providers.registry import ProviderRegistry

    config = ConfigManager().load()
    registry = ProviderRegistry()

    console.print(Panel.fit(
        f"Version: {__version__}\n"
        f"Config: {config.config_path}\n"
        f"Workspace: {config.workspace_path}\n"
        f"Active Providers: {len(registry.get_active_providers(config))}",
        title="🤖 chaobot Status",
        border_style="blue"
    ))


@cli.group(name="provider")
def provider_group() -> None:
    """Manage LLM providers."""
    pass


@provider_group.command(name="login")
@click.argument("provider_name")
def provider_login(provider_name: str) -> None:
    """OAuth login for providers."""
    console.print(f"Logging in to {provider_name}...")
    # TODO: Implement OAuth login


@cli.group(name="channels")
def channels_group() -> None:
    """Manage chat channels."""
    pass


@channels_group.command(name="login")
def channels_login() -> None:
    """Link channels (e.g., WhatsApp QR scan)."""
    console.print("Channel login...")
    # TODO: Implement channel login


@channels_group.command(name="status")
def channels_status() -> None:
    """Show channel status."""
    console.print("Channel status...")
    # TODO: Implement channel status


@cli.command(name="config")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8080, help="Port to listen on")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def config_ui(host: str, port: int, no_browser: bool) -> None:
    """Launch dashboard-based configuration UI."""
    import webbrowser
    from chaobot.dashboard.app import create_app

    app = create_app()
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
        title="🤖 chaobot Config",
        border_style="green"
    ))

    if not no_browser:
        # Open browser after a short delay
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host=host, port=port, debug=False)


@cli.group(name="session", invoke_without_command=True)
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=5000, help="Port to bind to")
@click.pass_context
def session_group(ctx, host: str, port: int) -> None:
    """Manage conversation sessions.
    
    Without subcommand: Start web UI for session management.
    With subcommand: Execute specific session command.
    """
    if ctx.invoked_subcommand is None:
        # Start web UI by default
        try:
            from chaobot.dashboard.session_manager import run_manager
            run_manager(host=host, port=port)
        except ImportError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Please install required dependencies:[/yellow]")
            console.print("  pip install flask")


@session_group.command(name="list")
def session_list() -> None:
    """List all conversation sessions."""
    import asyncio
    from chaobot.config.manager import ConfigManager
    from chaobot.agent.memory import MemoryManager

    config = ConfigManager().load()
    memory = MemoryManager(config)
    sessions = memory.get_all_sessions()

    if not sessions:
        console.print("No sessions found")
        return

    console.print(Panel.fit(
        "\n".join(f"  • {s}" for s in sorted(sessions)),
        title="📝 Sessions",
        border_style="blue"
    ))


@session_group.command(name="clear")
@click.argument("session_id", required=False)
@click.option("--all", "clear_all", is_flag=True, help="Clear all sessions")
def session_clear(session_id: str | None, clear_all: bool) -> None:
    """Clear conversation history for a session.

    Examples:
        chaobot session clear              # Clear default session
        chaobot session clear mysession    # Clear specific session
        chaobot session clear --all        # Clear all sessions
    """
    import asyncio
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


@session_group.command(name="ui")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=5000, help="Port to bind to")
def session_ui(host: str, port: int) -> None:
    """Start web interface for session management.

    Provides a web UI to view, edit, and manage conversation sessions.

    Examples:
        chaobot session                    # Start on default port 5000
        chaobot session --port 8080        # Start on port 8080
        chaobot session --host 0.0.0.0     # Allow external access
    """
    try:
        from chaobot.dashboard.session_manager import run_manager
        run_manager(host=host, port=port)
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please install required dependencies:[/yellow]")
        console.print("  pip install flask")


@cli.group(name="cron")
def cron_group() -> None:
    """Manage scheduled tasks."""
    pass


@cron_group.command(name="add")
@click.option("--name", required=True, help="Task name")
@click.option("--message", required=True, help="Message to send")
@click.option("--cron", help="Cron expression")
@click.option("--every", type=int, help="Run every N seconds")
def cron_add(name: str, message: str, cron: str | None, every: int | None) -> None:
    """Add a scheduled task."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    if cron:
        manager.add_cron(name, message, cron)
    elif every:
        manager.add_interval(name, message, every)
    else:
        click.echo("Either --cron or --every must be specified")
        return

    console.print(f"✅ Added task: {name}")


@cron_group.command(name="list")
def cron_list() -> None:
    """List scheduled tasks."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    tasks = manager.list_tasks()

    if not tasks:
        console.print("No scheduled tasks")
        return

    for task in tasks:
        console.print(f"  {task.id}: {task.name} - {task.schedule}")


@cron_group.command(name="remove")
@click.argument("task_id")
def cron_remove(task_id: str) -> None:
    """Remove a scheduled task."""
    from chaobot.cron.manager import CronManager

    manager = CronManager()
    manager.remove_task(task_id)
    console.print(f"✅ Removed task: {task_id}")


def main() -> None:
    """Main entry point."""
    cli()
