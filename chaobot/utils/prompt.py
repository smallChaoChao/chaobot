"""Enhanced prompt input using prompt_toolkit."""

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from pathlib import Path
from typing import Optional


class EnhancedPrompt:
    """Enhanced interactive prompt with history and key bindings."""

    def __init__(self, history_file: Optional[Path] = None):
        """Initialize enhanced prompt.

        Args:
            history_file: Path to history file for persistent history
        """
        # Set up history
        if history_file:
            history = FileHistory(str(history_file))
        else:
            history = None

        # Custom key bindings
        self.kb = KeyBindings()

        # Add Ctrl+C handling for canceling current input
        @self.kb.add('c-c')
        def _(event):
            """Ctrl+C clears current input or exits if empty."""
            if event.app.current_buffer.text:
                event.app.current_buffer.text = ""
            else:
                event.app.exit(exception=KeyboardInterrupt())

        # Add Ctrl+D handling for exit
        @self.kb.add('c-d')
        def _(event):
            """Ctrl+D exits if buffer is empty."""
            if not event.app.current_buffer.text:
                event.app.exit(exception=EOFError())

        # Add Ctrl+A for beginning of line
        @self.kb.add('c-a')
        def _(event):
            """Ctrl+A moves cursor to beginning of line."""
            event.app.current_buffer.cursor_position = 0

        # Add Ctrl+E for end of line
        @self.kb.add('c-e')
        def _(event):
            """Ctrl+E moves cursor to end of line."""
            event.app.current_buffer.cursor_position = len(
                event.app.current_buffer.text
            )

        # Add Ctrl+K to kill from cursor to end of line
        @self.kb.add('c-k')
        def _(event):
            """Ctrl+K deletes from cursor to end of line."""
            buffer = event.app.current_buffer
            buffer.text = buffer.text[:buffer.cursor_position]

        # Add Ctrl+U to kill from beginning to cursor
        @self.kb.add('c-u')
        def _(event):
            """Ctrl+U deletes from beginning to cursor."""
            buffer = event.app.current_buffer
            buffer.text = buffer.text[buffer.cursor_position:]
            buffer.cursor_position = 0

        # Add Ctrl+W to delete previous word
        @self.kb.add('c-w')
        def _(event):
            """Ctrl+W deletes previous word."""
            buffer = event.app.current_buffer
            text = buffer.text[:buffer.cursor_position]
            # Find start of previous word
            pos = len(text) - 1
            while pos >= 0 and text[pos].isspace():
                pos -= 1
            while pos >= 0 and not text[pos].isspace():
                pos -= 1
            new_text = text[:pos + 1] + buffer.text[buffer.cursor_position:]
            buffer.text = new_text
            buffer.cursor_position = pos + 1

        # Add Ctrl+L to clear screen (handled by rich console)
        @self.kb.add('c-l')
        def _(event):
            """Ctrl+L clears screen."""
            # Just pass through, let the terminal handle it
            pass

        # Create prompt session
        # Note: mouse_support is disabled to allow terminal text selection,
        # scrolling, and copy/paste operations. This is a trade-off:
        # - Disabled: Normal terminal mouse behavior (select, scroll, copy)
        # - Enabled: Can use mouse to position cursor, but loses terminal mouse features
        self.session = PromptSession(
            history=history,
            key_bindings=self.kb,
            enable_history_search=True,
            enable_suspend=True,
            mouse_support=False,
        )

    def prompt(
        self,
        message: str = "> ",
        multiline: bool = False,
        default: str = ""
    ) -> str:
        """Get user input with enhanced features.

        Args:
            message: Prompt message
            multiline: Allow multiline input
            default: Default text

        Returns:
            User input string
        """
        try:
            if multiline:
                # For multiline, use Alt+Enter to submit
                text = self.session.prompt(
                    message,
                    multiline=True,
                    default=default,
                )
            else:
                text = self.session.prompt(
                    message,
                    default=default,
                )
            return text.strip()
        except KeyboardInterrupt:
            raise
        except EOFError:
            raise


def create_prompt(workspace_path: Optional[Path] = None) -> EnhancedPrompt:
    """Create an enhanced prompt with history.

    Args:
        workspace_path: Path to workspace for history file

    Returns:
        EnhancedPrompt instance
    """
    if workspace_path:
        history_dir = workspace_path / ".history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / "chaobot_history"
    else:
        history_file = None

    return EnhancedPrompt(history_file=history_file)
