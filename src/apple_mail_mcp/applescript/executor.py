"""AppleScript execution via osascript subprocess."""

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class AppleScriptError(Exception):
    """Raised when AppleScript execution fails."""

    pass


class AppleScriptExecutor:
    """Executes AppleScript code via osascript."""

    def run(self, script: str, timeout: int = 30) -> str:
        """
        Execute an AppleScript and return the result.

        Args:
            script: The AppleScript code to execute
            timeout: Maximum execution time in seconds

        Returns:
            The stdout from the script execution

        Raises:
            AppleScriptError: If the script fails or times out
        """
        logger.debug("Executing AppleScript:\n%s", script)

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown AppleScript error"
                logger.error("AppleScript failed: %s", error_msg)
                raise AppleScriptError(error_msg)

            output = result.stdout.strip()
            logger.debug("AppleScript result: %s", output[:500] if output else "(empty)")
            return output

        except subprocess.TimeoutExpired:
            logger.error("AppleScript timed out after %d seconds", timeout)
            raise AppleScriptError(f"Script timed out after {timeout} seconds")

    def run_script_file(
        self, script_path: str, args: Optional[list[str]] = None, timeout: int = 30
    ) -> str:
        """
        Execute an AppleScript file.

        Args:
            script_path: Path to the .scpt or .applescript file
            args: Optional arguments to pass to the script
            timeout: Maximum execution time in seconds

        Returns:
            The stdout from the script execution
        """
        cmd = ["osascript", script_path]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown AppleScript error"
                raise AppleScriptError(error_msg)

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise AppleScriptError(f"Script timed out after {timeout} seconds")
