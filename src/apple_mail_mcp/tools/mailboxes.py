"""Mailbox listing tool."""

import logging
from dataclasses import dataclass

from ..applescript import RECORD_SEP
from ..applescript.executor import AppleScriptExecutor
from ..applescript.scripts import Scripts

logger = logging.getLogger(__name__)


@dataclass
class Mailbox:
    """Represents a mailbox/folder."""

    path: str
    message_count: int
    unread_count: int


def list_mailboxes(
    executor: AppleScriptExecutor,
    account_name: str,
    include_nested: bool = True,
) -> list[Mailbox]:
    """
    List mailboxes for a specific mail account.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        include_nested: Whether to include nested mailboxes recursively

    Returns:
        List of Mailbox objects
    """
    script = Scripts.list_mailboxes(account_name, include_nested)
    output = executor.run(script)

    mailboxes = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split(RECORD_SEP)
        if len(parts) >= 3:
            path = parts[0].strip()
            try:
                message_count = int(parts[1].strip())
            except ValueError:
                message_count = 0
            try:
                unread_count = int(parts[2].strip())
            except ValueError:
                unread_count = 0

            mailboxes.append(
                Mailbox(
                    path=path,
                    message_count=message_count,
                    unread_count=unread_count,
                )
            )

    logger.info("Found %d mailboxes for account '%s'", len(mailboxes), account_name)
    return mailboxes


def create_mailbox(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_name: str,
    parent_mailbox: str | None = None,
) -> dict:
    """
    Create a new mailbox in an account.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_name: Name for the new mailbox
        parent_mailbox: Optional parent mailbox path for nested creation

    Returns:
        Dict with success status
    """
    script = Scripts.create_mailbox(account_name, mailbox_name, parent_mailbox)
    executor.run(script)

    location = f"{parent_mailbox}/{mailbox_name}" if parent_mailbox else mailbox_name
    logger.info("Created mailbox '%s' in account '%s'", location, account_name)

    return {
        "success": True,
        "message": f"Mailbox '{location}' created",
    }


def rename_mailbox(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    new_name: str,
) -> dict:
    """
    Rename a mailbox.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Path to the mailbox to rename
        new_name: New name for the mailbox

    Returns:
        Dict with success status
    """
    script = Scripts.rename_mailbox(account_name, mailbox_path, new_name)
    executor.run(script)

    logger.info(
        "Renamed mailbox '%s' to '%s' in account '%s'",
        mailbox_path,
        new_name,
        account_name,
    )

    return {
        "success": True,
        "message": f"Mailbox '{mailbox_path}' renamed to '{new_name}'",
    }
