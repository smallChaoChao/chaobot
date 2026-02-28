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
def gateway() -> None:
    """Start the gateway (connects to enabled channels)."""
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
