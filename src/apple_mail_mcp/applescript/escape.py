"""AppleScript string escaping and delimiter constants."""

from __future__ import annotations

# Delimiter constants - using ASCII control characters to avoid collision with email content
# These characters are extremely unlikely to appear in email subjects, bodies, or sender names
RECORD_SEP = chr(30)  # Record Separator - separates fields within a record
UNIT_SEP = chr(31)    # Unit Separator - separates message fields (like |||FIELD|||)
GROUP_SEP = chr(29)   # Group Separator - separates messages (like |||MSG|||)


def escape_applescript_string(value: str | None) -> str:
    """
    Escape a string for safe use in AppleScript double-quoted strings.

    This prevents AppleScript injection attacks by properly escaping
    special characters that could break out of string literals.

    Args:
        value: The string to escape (or None)

    Returns:
        The escaped string safe for AppleScript interpolation
    """
    if value is None:
        return ""

    # Escape backslashes first (must be first to avoid double-escaping)
    result = value.replace("\\", "\\\\")
    # Escape double quotes
    result = result.replace('"', '\\"')
    # Escape tabs
    result = result.replace("\t", "\\t")
    # Escape newlines
    result = result.replace("\n", "\\n")
    # Escape carriage returns
    result = result.replace("\r", "\\r")

    return result


# Short alias for convenience in scripts.py
esc = escape_applescript_string
