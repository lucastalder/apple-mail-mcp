"""Apple Mail MCP Server - Main entry point."""

import logging
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from .applescript.executor import AppleScriptExecutor, AppleScriptError
from .tools.accounts import list_accounts as _list_accounts
from .tools.mailboxes import list_mailboxes as _list_mailboxes
from .tools.messages import (
    list_messages as _list_messages,
    read_messages as _read_messages,
    search_messages as _search_messages,
)
from .tools.operations import (
    bulk_move_messages as _move_messages,
    bulk_set_status as _set_messages_status,
)

# Configure logging to file (never print to stdout - it corrupts JSON-RPC)
logging.basicConfig(
    filename="/tmp/apple-mail-mcp.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the MCP server
mcp = FastMCP("Apple Mail")

# Shared executor instance
executor = AppleScriptExecutor()


@mcp.tool()
def list_accounts() -> list[dict]:
    """
    List all mail accounts configured in Apple Mail.

    Returns a list of accounts with their name, email, enabled status,
    account type, and whether they appear to be Gmail accounts.
    """
    try:
        accounts = _list_accounts(executor)
        return [asdict(acc) for acc in accounts]
    except AppleScriptError as e:
        logger.error("Failed to list accounts: %s", e)
        return [{"error": str(e)}]


@mcp.tool()
def list_mailboxes(account_name: str, include_nested: bool = True) -> list[dict]:
    """
    List mailboxes (folders) for a specific mail account.

    Args:
        account_name: The name of the mail account (as shown in Mail.app)
        include_nested: Whether to include nested mailboxes recursively (default: True)

    Returns a list of mailboxes with their path, message count, and unread count.
    """
    try:
        mailboxes = _list_mailboxes(executor, account_name, include_nested)
        return [asdict(mb) for mb in mailboxes]
    except AppleScriptError as e:
        logger.error("Failed to list mailboxes for '%s': %s", account_name, e)
        return [{"error": str(e)}]


@mcp.tool()
def list_messages(
    account_name: str,
    mailbox_path: str,
    limit: int = 50,
    unread_only: bool = False,
    flagged_only: bool = False,
) -> list[dict]:
    """
    List messages in a mailbox with optional filtering.

    Args:
        account_name: The name of the mail account
        mailbox_path: Path to the mailbox (e.g., "INBOX", "Archive")
        limit: Maximum number of messages to return (default: 50)
        unread_only: Only return unread messages (default: False)
        flagged_only: Only return flagged messages (default: False)

    Returns a list of message summaries with id, subject, sender, date,
    read status, and flagged status. Use the message id for other operations.
    """
    try:
        messages = _list_messages(
            executor, account_name, mailbox_path, limit, unread_only, flagged_only
        )
        return [asdict(msg) for msg in messages]
    except AppleScriptError as e:
        logger.error(
            "Failed to list messages in '%s/%s': %s", account_name, mailbox_path, e
        )
        return [{"error": str(e)}]


@mcp.tool()
def read_messages(
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
) -> list[dict]:
    """
    Read the full content of one or more messages.

    Args:
        account_name: The name of the mail account
        mailbox_path: Path to the mailbox containing the messages
        message_ids: List of message IDs to read (from list_messages or search_messages)

    Returns a list of full messages including subject, sender, recipients (to, cc),
    date, read/flagged status, and the message content/body.
    """
    try:
        messages = _read_messages(executor, account_name, mailbox_path, message_ids)
        return [asdict(msg) if hasattr(msg, "__dataclass_fields__") else msg for msg in messages]
    except AppleScriptError as e:
        logger.error(
            "Failed to read messages in '%s/%s': %s",
            account_name,
            mailbox_path,
            e,
        )
        return [{"error": str(e)}]


@mcp.tool()
def search_messages(
    account_name: str,
    mailbox_path: str,
    sender_contains: str | None = None,
    subject_contains: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Search messages by sender and/or subject.

    Args:
        account_name: The name of the mail account
        mailbox_path: Path to the mailbox to search
        sender_contains: Filter messages where sender contains this string
        subject_contains: Filter messages where subject contains this string
        limit: Maximum number of messages to return (default: 50)

    Returns a list of message summaries matching the search criteria.
    At least one of sender_contains or subject_contains should be provided.
    """
    try:
        messages = _search_messages(
            executor, account_name, mailbox_path, sender_contains, subject_contains, limit
        )
        return [asdict(msg) for msg in messages]
    except AppleScriptError as e:
        logger.error(
            "Failed to search messages in '%s/%s': %s",
            account_name,
            mailbox_path,
            e,
        )
        return [{"error": str(e)}]


@mcp.tool()
def move_messages(
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
    destination_mailbox: str,
) -> dict:
    """
    Move one or more messages to another mailbox.

    Args:
        account_name: The name of the mail account
        mailbox_path: Current mailbox path containing the messages
        message_ids: List of message IDs to move
        destination_mailbox: The destination mailbox path

    Returns success count and new message IDs (IDs change after moving).
    """
    try:
        return _move_messages(
            executor,
            account_name,
            mailbox_path,
            message_ids,
            destination_mailbox,
        )
    except AppleScriptError as e:
        logger.error(
            "Failed to move messages from '%s/%s' to '%s': %s",
            account_name,
            mailbox_path,
            destination_mailbox,
            e,
        )
        return {"success": False, "error": str(e)}


@mcp.tool()
def set_messages_status(
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
    read_status: bool | None = None,
    flagged_status: bool | None = None,
) -> dict:
    """
    Set the read and/or flagged status for one or more messages.

    Args:
        account_name: The name of the mail account
        mailbox_path: Path to the mailbox containing the messages
        message_ids: List of message IDs to update
        read_status: Set to True to mark as read, False for unread, None to skip
        flagged_status: Set to True to flag, False to unflag, None to skip

    Returns success status and count of updated messages.
    """
    try:
        return _set_messages_status(
            executor,
            account_name,
            mailbox_path,
            message_ids,
            read_status,
            flagged_status,
        )
    except AppleScriptError as e:
        logger.error(
            "Failed to set status in '%s/%s': %s",
            account_name,
            mailbox_path,
            e,
        )
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server."""
    logger.info("Starting Apple Mail MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
