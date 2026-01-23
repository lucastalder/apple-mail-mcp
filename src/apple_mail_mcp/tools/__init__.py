"""Mail operation tools."""

from .accounts import list_accounts
from .mailboxes import list_mailboxes, create_mailbox, rename_mailbox
from .messages import list_messages, read_message, read_messages, search_messages
from .operations import move_message, set_message_status, bulk_move_messages, bulk_set_status

__all__ = [
    "list_accounts",
    "list_mailboxes",
    "create_mailbox",
    "rename_mailbox",
    "list_messages",
    "read_message",
    "read_messages",
    "search_messages",
    "move_message",
    "set_message_status",
    "bulk_move_messages",
    "bulk_set_status",
]
