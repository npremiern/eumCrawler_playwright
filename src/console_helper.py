"""Console helper for handling output in both GUI and CLI modes."""

import os
import sys


class DummyConsole:
    """Dummy console that does nothing (for GUI mode)."""
    
    def print(self, *args, **kwargs):
        """Ignore all print calls."""
        pass


class PrintConsole:
    """Simple print-based console (for CLI mode without Rich)."""
    
    def print(self, *args, **kwargs):
        """Print to stdout using built-in print."""
        print(*args, **kwargs)


class RichConsole:
    """Rich console wrapper (for CLI mode with Rich library)."""
    
    def __init__(self):
        """Initialize Rich console."""
        from rich.console import Console as RichLib
        self._console = RichLib(legacy_windows=False)
    
    def print(self, *args, **kwargs):
        """Print using Rich console."""
        self._console.print(*args, **kwargs)


# Lazy console initialization
_console = None


def get_console():
    """
    Get console instance (lazy initialization).
    
    Returns:
        Console instance appropriate for the current mode (GUI or CLI).
    """
    global _console
    if _console is None:
        # Check if we're in GUI mode
        if os.environ.get('EUMCRAWL_GUI_MODE') == '1':
            _console = DummyConsole()
        else:
            # CLI mode - try to use Rich console
            try:
                _console = RichConsole()
            except Exception:
                # If Rich is not available, fall back to simple print
                _console = PrintConsole()
    return _console


class ConsoleProxy:
    """Console proxy that uses lazy initialization."""
    
    def print(self, *args, **kwargs):
        """Proxy print call to the actual console."""
        get_console().print(*args, **kwargs)


# Create a global console instance
console = ConsoleProxy()
