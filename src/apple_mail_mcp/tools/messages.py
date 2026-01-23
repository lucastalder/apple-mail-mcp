"""Message listing and reading tools."""

import logging
from dataclasses import dataclass
from typing import TypedDict

from ..applescript import RECORD_SEP, UNIT_SEP, GROUP_SEP
from ..applescript.executor import AppleScriptExecutor
from ..applescript.scripts import Scripts

logger = logging.getLogger(__name__)


@dataclass
class MessageSummary:
    """Summary information about a message."""

    id: int
    subject: str
    sender: str
    date: str
    is_read: bool
    is_flagged: bool


@dataclass
class Message:
    """Full message content."""

    id: int
    subject: str
    sender: str
    to: str
    cc: str
    date: str
    is_read: bool
    is_flagged: bool
    content: str


class PaginatedMessages(TypedDict):
    """Paginated message list with metadata."""
    messages: list[MessageSummary] | list[Message]
    total: int
    offset: int
    limit: int
    has_more: bool


def _parse_total_count(output: str) -> tuple[int, str]:
    """Extract total count from output and return remaining content.

    Args:
        output: Raw AppleScript output starting with "TOTAL:N" line

    Returns:
        Tuple of (total_count, remaining_output)
    """
    lines = output.split("\n", 1)
    total = 0
    remaining = output

    if lines and lines[0].startswith("TOTAL:"):
        try:
            total = int(lines[0][6:])
        except ValueError:
            pass
        remaining = lines[1] if len(lines) > 1 else ""

    return total, remaining


def list_messages(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    flagged_only: bool = False,
    include_content: bool = False,
    content_limit: int | None = None,
) -> PaginatedMessages:
    """
    List messages in a mailbox with optional filtering.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Path to the mailbox (e.g., "INBOX")
        limit: Maximum number of messages to return
        offset: Number of messages to skip (for pagination)
        unread_only: Only return unread messages
        flagged_only: Only return flagged messages
        include_content: If True, include message body content (returns Message objects)
        content_limit: Maximum characters per message body (only used with include_content)

    Returns:
        PaginatedMessages dict with messages list and pagination metadata
    """
    script = Scripts.list_messages(
        account_name, mailbox_path, limit, offset, unread_only, flagged_only,
        include_content, content_limit
    )
    # Use longer timeout when fetching content
    timeout = 120 if include_content else 60
    output = executor.run(script, timeout=timeout)

    # Extract total count
    total, output = _parse_total_count(output)

    messages: list[MessageSummary] | list[Message] = []

    if include_content:
        # Parse the GROUP_SEP / UNIT_SEP format (same as read_messages)
        msg_blocks = output.split(GROUP_SEP)
        for block in msg_blocks:
            if not block.strip():
                continue

            parts = block.split(UNIT_SEP)
            if len(parts) < 9:
                continue

            try:
                msg_id = int(parts[0].strip())
            except ValueError:
                continue

            content = parts[8] if len(parts) > 8 else ""
            # Note: content_limit is already applied in AppleScript, but add "..." indicator
            if content_limit is not None and len(content) > content_limit:
                content = content + "..."

            messages.append(
                Message(
                    id=msg_id,
                    subject=parts[1].strip(),
                    sender=parts[2].strip(),
                    to=parts[3].strip(),
                    cc=parts[4].strip(),
                    date=parts[5].strip(),
                    is_read=parts[6].strip().lower() == "true",
                    is_flagged=parts[7].strip().lower() == "true",
                    content=content,
                )
            )
    else:
        # Parse the simple RECORD_SEP format (summary only)
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split(RECORD_SEP)
            if len(parts) >= 6:
                try:
                    msg_id = int(parts[0].strip())
                except ValueError:
                    continue

                subject = parts[1].strip()
                sender = parts[2].strip()
                date = parts[3].strip()
                is_read = parts[4].strip().lower() == "true"
                is_flagged = parts[5].strip().lower() == "true"

                messages.append(
                    MessageSummary(
                        id=msg_id,
                        subject=subject,
                        sender=sender,
                        date=date,
                        is_read=is_read,
                        is_flagged=is_flagged,
                    )
                )

    logger.info(
        "Found %d messages in %s/%s (total: %d)", len(messages), account_name, mailbox_path, total
    )

    return {
        "messages": messages,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(messages) < total,
    }


def read_message(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_id: int,
) -> Message:
    """
    Read full message content by ID.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Path to the mailbox
        message_id: AppleScript message ID

    Returns:
        Message object with full content
    """
    script = Scripts.read_message(account_name, mailbox_path, message_id)
    output = executor.run(script, timeout=60)

    parts = output.split(UNIT_SEP)
    if len(parts) < 9:
        raise ValueError(f"Invalid message response format: got {len(parts)} parts")

    try:
        msg_id = int(parts[0].strip())
    except ValueError:
        msg_id = message_id

    return Message(
        id=msg_id,
        subject=parts[1].strip(),
        sender=parts[2].strip(),
        to=parts[3].strip(),
        cc=parts[4].strip(),
        date=parts[5].strip(),
        is_read=parts[6].strip().lower() == "true",
        is_flagged=parts[7].strip().lower() == "true",
        content=parts[8] if len(parts) > 8 else "",
    )


def read_messages(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
    content_limit: int | None = None,
) -> list[Message | dict]:
    """
    Read multiple messages by their IDs in a single call.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Path to the mailbox
        message_ids: List of AppleScript message IDs
        content_limit: Maximum characters to return per message body (None = full content)

    Returns:
        List of Message objects (or error dicts for failed reads)
    """
    script = Scripts.read_messages(account_name, mailbox_path, message_ids)
    output = executor.run(script, timeout=120)

    messages: list[Message | dict] = []
    msg_blocks = output.split(GROUP_SEP)

    for block in msg_blocks:
        if not block.strip():
            continue

        parts = block.split(UNIT_SEP)
        if len(parts) < 2:
            continue

        try:
            msg_id = int(parts[0].strip())
        except ValueError:
            continue

        # Check for error
        if len(parts) >= 3 and parts[1].strip() == "ERROR":
            messages.append({"id": msg_id, "error": parts[2].strip()})
            continue

        if len(parts) >= 9:
            content = parts[8] if len(parts) > 8 else ""
            if content_limit is not None and len(content) > content_limit:
                content = content[:content_limit] + "..."
            messages.append(
                Message(
                    id=msg_id,
                    subject=parts[1].strip(),
                    sender=parts[2].strip(),
                    to=parts[3].strip(),
                    cc=parts[4].strip(),
                    date=parts[5].strip(),
                    is_read=parts[6].strip().lower() == "true",
                    is_flagged=parts[7].strip().lower() == "true",
                    content=content,
                )
            )

    logger.info(
        "Read %d messages from %s/%s", len(messages), account_name, mailbox_path
    )
    return messages


def search_messages(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    sender_contains: str | None = None,
    subject_contains: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedMessages:
    """
    Search messages by sender and/or subject.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Path to the mailbox
        sender_contains: Filter by sender containing this string
        subject_contains: Filter by subject containing this string
        limit: Maximum number of messages to return
        offset: Number of messages to skip (for pagination)

    Returns:
        PaginatedMessages dict with messages list and pagination metadata
    """
    script = Scripts.search_messages(
        account_name, mailbox_path, sender_contains, subject_contains, limit, offset
    )
    output = executor.run(script, timeout=120)

    # Extract total count
    total, output = _parse_total_count(output)

    messages: list[MessageSummary] = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split(RECORD_SEP)
        if len(parts) >= 6:
            try:
                msg_id = int(parts[0].strip())
            except ValueError:
                continue

            messages.append(
                MessageSummary(
                    id=msg_id,
                    subject=parts[1].strip(),
                    sender=parts[2].strip(),
                    date=parts[3].strip(),
                    is_read=parts[4].strip().lower() == "true",
                    is_flagged=parts[5].strip().lower() == "true",
                )
            )

    logger.info(
        "Search found %d messages in %s/%s (total: %d)", len(messages), account_name, mailbox_path, total
    )

    return {
        "messages": messages,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(messages) < total,
    }
