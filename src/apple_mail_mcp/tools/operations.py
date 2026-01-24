"""Message operation tools (move, set status)."""

import logging

from ..applescript import RECORD_SEP
from ..applescript.executor import AppleScriptExecutor
from ..applescript.scripts import Scripts

logger = logging.getLogger(__name__)


def move_message(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_id: int,
    destination_mailbox: str,
) -> dict:
    """
    Move a message to another mailbox.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Source mailbox path
        message_id: AppleScript message ID
        destination_mailbox: Destination mailbox path

    Returns:
        Dict with success status
    """
    script = Scripts.move_message(
        account_name, mailbox_path, message_id, destination_mailbox
    )
    output = executor.run(script)

    # Parse the new message ID from output (format: "moved{RECORD_SEP}{new_id}")
    new_id = None
    if RECORD_SEP in output:
        parts = output.split(RECORD_SEP)
        if len(parts) >= 2:
            try:
                new_id = int(parts[1])
            except ValueError:
                pass

    result = {
        "success": True,
        "message": f"Message {message_id} moved from '{mailbox_path}' to '{destination_mailbox}'",
    }

    if new_id is not None:
        result["new_message_id"] = new_id

    logger.info(
        "Moved message %d from '%s' to '%s' in account '%s'",
        message_id,
        mailbox_path,
        destination_mailbox,
        account_name,
    )

    return result


def set_message_status(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_id: int,
    read_status: bool | None = None,
    flagged_status: bool | None = None,
) -> dict:
    """
    Set read and/or flagged status of a message.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Mailbox path
        message_id: AppleScript message ID
        read_status: Set to True (read) or False (unread), None to leave unchanged
        flagged_status: Set to True (flagged) or False (unflagged), None to leave unchanged

    Returns:
        Dict with success status and what was changed
    """
    changes = []

    if read_status is not None:
        script = Scripts.set_read_status(
            account_name, mailbox_path, message_id, read_status
        )
        executor.run(script)
        status_str = "read" if read_status else "unread"
        changes.append(f"marked as {status_str}")
        logger.info(
            "Set message %d in '%s/%s' to %s",
            message_id,
            account_name,
            mailbox_path,
            status_str,
        )

    if flagged_status is not None:
        script = Scripts.set_flagged_status(
            account_name, mailbox_path, message_id, flagged_status
        )
        executor.run(script)
        status_str = "flagged" if flagged_status else "unflagged"
        changes.append(status_str)
        logger.info(
            "Set message %d in '%s/%s' to %s",
            message_id,
            account_name,
            mailbox_path,
            status_str,
        )

    if not changes:
        return {
            "success": True,
            "message": "No changes requested",
        }

    return {
        "success": True,
        "message": f"Message {message_id} {', '.join(changes)}",
    }


def bulk_move_messages(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
    destination_mailbox: str,
) -> dict:
    """
    Move multiple messages to another mailbox.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Source mailbox path
        message_ids: List of message IDs to move
        destination_mailbox: Destination mailbox path

    Returns:
        Dict with success count and details of moved messages
    """
    script = Scripts.bulk_move_messages(
        account_name, mailbox_path, message_ids, destination_mailbox
    )
    output = executor.run(script, timeout=120)

    results = []
    success_count = 0
    error_count = 0

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split(RECORD_SEP)
        if len(parts) >= 3:
            try:
                old_id = int(parts[0].strip())
                new_id = int(parts[1].strip())
                status = parts[2].strip()

                if status == "success":
                    success_count += 1
                    results.append({
                        "old_id": old_id,
                        "new_id": new_id,
                        "success": True,
                    })
                else:
                    error_count += 1
                    results.append({
                        "old_id": old_id,
                        "success": False,
                        "error": status,
                    })
            except ValueError:
                continue

    logger.info(
        "Bulk moved %d/%d messages from '%s/%s' to '%s'",
        success_count,
        len(message_ids),
        account_name,
        mailbox_path,
        destination_mailbox,
    )

    return {
        "success": error_count == 0,
        "moved_count": success_count,
        "error_count": error_count,
        "total": len(message_ids),
        "results": results,
    }


def bulk_set_status(
    executor: AppleScriptExecutor,
    account_name: str,
    mailbox_path: str,
    message_ids: list[int],
    read_status: bool | None = None,
    flagged_status: bool | None = None,
) -> dict:
    """
    Set read and/or flagged status for multiple messages.

    Args:
        executor: The AppleScript executor instance
        account_name: Name of the mail account
        mailbox_path: Mailbox path
        message_ids: List of message IDs to update
        read_status: Set to True (read) or False (unread), None to skip
        flagged_status: Set to True (flagged) or False (unflagged), None to skip

    Returns:
        Dict with success status and counts
    """
    results = []

    if read_status is not None:
        script = Scripts.bulk_set_read_status(
            account_name, mailbox_path, message_ids, read_status
        )
        output = executor.run(script, timeout=120)
        status_str = "read" if read_status else "unread"
        results.append(f"marked {status_str}: {output}")
        logger.info(
            "Bulk set %d messages in '%s/%s' to %s",
            len(message_ids),
            account_name,
            mailbox_path,
            status_str,
        )

    if flagged_status is not None:
        script = Scripts.bulk_set_flagged_status(
            account_name, mailbox_path, message_ids, flagged_status
        )
        output = executor.run(script, timeout=120)
        status_str = "flagged" if flagged_status else "unflagged"
        results.append(f"{status_str}: {output}")
        logger.info(
            "Bulk set %d messages in '%s/%s' to %s",
            len(message_ids),
            account_name,
            mailbox_path,
            status_str,
        )

    if not results:
        return {
            "success": True,
            "message": "No changes requested",
        }

    return {
        "success": True,
        "message": "; ".join(results),
        "total_messages": len(message_ids),
    }
