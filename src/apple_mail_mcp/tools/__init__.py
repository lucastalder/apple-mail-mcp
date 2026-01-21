"""Mail operation tools."""

from .accounts import list_accounts
from .mailboxes import list_mailboxes
from .messages import list_messages, read_message
from .operations import move_message, set_message_status

__all__ = [
    "list_accounts",
    "list_mailboxes",
    "list_messages",
    "read_message",
    "move_message",
    "set_message_status",
]
