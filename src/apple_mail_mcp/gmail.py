"""Gmail account detection and handling."""

import logging

logger = logging.getLogger(__name__)

GMAIL_PATTERNS = ["gmail", "google", "imap.gmail.com", "googlemail"]


def is_gmail_account(server_name: str) -> bool:
    """
    Check if an account appears to be a Gmail account based on server name.

    Args:
        server_name: The IMAP/SMTP server name for the account

    Returns:
        True if the server appears to be Gmail
    """
    if not server_name:
        return False

    server_lower = server_name.lower()
    return any(pattern in server_lower for pattern in GMAIL_PATTERNS)


def is_gmail_account_by_email(email: str) -> bool:
    """
    Check if an account appears to be Gmail based on email address.

    Args:
        email: The email address

    Returns:
        True if the email appears to be Gmail
    """
    if not email:
        return False

    email_lower = email.lower()
    return email_lower.endswith("@gmail.com") or email_lower.endswith("@googlemail.com")


def get_gmail_move_warning() -> str:
    """
    Get the warning message for moving messages in Gmail accounts.

    Returns:
        Warning string about Gmail label behavior
    """
    return (
        "Note: Gmail uses labels instead of folders. When moving messages from Inbox "
        "via AppleScript, the Inbox label may not be removed, causing the message to "
        "appear in both locations. This is a known Mail.app/AppleScript limitation."
    )
