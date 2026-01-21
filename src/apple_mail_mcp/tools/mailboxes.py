"""Mailbox listing tool."""

import logging
from dataclasses import dataclass

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

        parts = line.split("|||")
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
