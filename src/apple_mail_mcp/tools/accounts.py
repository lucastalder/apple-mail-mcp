"""Account listing tool."""

import logging
from dataclasses import dataclass

from ..applescript.executor import AppleScriptExecutor
from ..applescript.scripts import Scripts
from ..gmail import is_gmail_account_by_email

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Represents a mail account."""

    name: str
    email: str
    enabled: bool
    account_type: str
    is_gmail: bool


def list_accounts(executor: AppleScriptExecutor) -> list[Account]:
    """
    List all mail accounts configured in Apple Mail.

    Args:
        executor: The AppleScript executor instance

    Returns:
        List of Account objects
    """
    script = Scripts.list_accounts()
    output = executor.run(script)

    accounts = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split("|||")
        if len(parts) >= 4:
            name = parts[0].strip()
            email = parts[1].strip()
            enabled = parts[2].strip().lower() == "true"
            account_type = parts[3].strip()

            accounts.append(
                Account(
                    name=name,
                    email=email,
                    enabled=enabled,
                    account_type=account_type,
                    is_gmail=is_gmail_account_by_email(email),
                )
            )

    logger.info("Found %d mail accounts", len(accounts))
    return accounts
