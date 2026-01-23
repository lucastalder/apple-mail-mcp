"""Account listing tool."""

import logging
from dataclasses import dataclass

from ..applescript import RECORD_SEP
from ..applescript.executor import AppleScriptExecutor, AppleScriptError
from ..applescript.scripts import Scripts
from ..gmail import is_gmail_account

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """Represents a mail account."""

    name: str
    email: str
    enabled: bool
    account_type: str
    is_gmail: bool


def _check_is_gmail(executor: AppleScriptExecutor, account_name: str) -> bool:
    """Check if account uses Gmail/Google servers."""
    try:
        script = Scripts.get_account_server(account_name)
        server_name = executor.run(script, timeout=10).strip()
        return is_gmail_account(server_name)
    except AppleScriptError:
        return False


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

        parts = line.split(RECORD_SEP)
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
                    is_gmail=_check_is_gmail(executor, name),
                )
            )

    logger.info("Found %d mail accounts", len(accounts))
    return accounts
