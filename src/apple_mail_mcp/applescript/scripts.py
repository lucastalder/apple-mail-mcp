"""AppleScript templates for Apple Mail operations."""

from .escape import esc, RECORD_SEP, UNIT_SEP, GROUP_SEP


class Scripts:
    """Collection of AppleScript templates for Mail.app interaction."""

    @staticmethod
    def list_accounts() -> str:
        """List all mail accounts with their details."""
        return f'''
tell application "Mail"
    set output to ""
    repeat with acc in accounts
        set accName to name of acc
        set accEmail to email addresses of acc as string
        set accEnabled to enabled of acc
        set accType to account type of acc as string
        set output to output & accName & (ASCII character 30) & accEmail & (ASCII character 30) & accEnabled & (ASCII character 30) & accType & linefeed
    end repeat
    return output
end tell
'''

    @staticmethod
    def list_mailboxes(account_name: str, include_nested: bool = True) -> str:
        """List mailboxes for a specific account."""
        account_name = esc(account_name)
        if include_nested:
            return f'''
tell application "Mail"
    set output to ""
    set acc to account "{account_name}"

    -- Use a queue-based approach for iterative traversal
    set mbQueue to {{}}
    set prefixQueue to {{}}

    -- Initialize with top-level mailboxes
    repeat with mb in mailboxes of acc
        set end of mbQueue to mb
        set end of prefixQueue to ""
    end repeat

    -- Process queue
    repeat while (count of mbQueue) > 0
        set currentMb to item 1 of mbQueue
        set currentPrefix to item 1 of prefixQueue

        -- Remove first items from queues
        if (count of mbQueue) > 1 then
            set mbQueue to items 2 thru -1 of mbQueue
            set prefixQueue to items 2 thru -1 of prefixQueue
        else
            set mbQueue to {{}}
            set prefixQueue to {{}}
        end if

        -- Get mailbox info
        set mbName to name of currentMb
        set fullPath to currentPrefix & mbName
        set msgCount to count of messages of currentMb
        set unreadCount to unread count of currentMb
        set output to output & fullPath & (ASCII character 30) & msgCount & (ASCII character 30) & unreadCount & linefeed

        -- Add child mailboxes to queue
        try
            repeat with childMb in mailboxes of currentMb
                set end of mbQueue to childMb
                set end of prefixQueue to fullPath & "/"
            end repeat
        end try
    end repeat

    return output
end tell
'''
        else:
            return f'''
tell application "Mail"
    set output to ""
    set acc to account "{account_name}"

    repeat with mb in mailboxes of acc
        set mbName to name of mb
        set msgCount to count of messages of mb
        set unreadCount to unread count of mb
        set output to output & mbName & (ASCII character 30) & msgCount & (ASCII character 30) & unreadCount & linefeed
    end repeat

    return output
end tell
'''

    @staticmethod
    def list_messages(
        account_name: str,
        mailbox_path: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        flagged_only: bool = False,
        include_content: bool = False,
        content_limit: int | None = None,
    ) -> str:
        """List messages in a mailbox with optional filtering and content."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)

        filter_condition = ""
        if unread_only and flagged_only:
            filter_condition = "whose read status is false and flagged status is true"
        elif unread_only:
            filter_condition = "whose read status is false"
        elif flagged_only:
            filter_condition = "whose flagged status is true"

        if include_content:
            # Include full message data with content
            content_truncation = ""
            if content_limit is not None:
                content_truncation = f'''
                if (count of msgContent) > {content_limit} then
                    set msgContent to text 1 thru {content_limit} of msgContent
                end if'''

            return f'''
tell application "Mail"
    set output to ""
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc

    set msgList to (messages of mb {filter_condition})
    set totalCount to count of msgList
    set startIdx to {offset} + 1
    set endIdx to {offset} + {limit}
    if endIdx > totalCount then set endIdx to totalCount
    if startIdx > totalCount then set startIdx to totalCount + 1

    -- Output total count as first line
    set output to "TOTAL:" & totalCount & linefeed

    repeat with i from startIdx to endIdx
        set msg to item i of msgList
        set msgId to id of msg
        set msgSubject to subject of msg
        set msgSender to sender of msg
        set msgDate to date received of msg as string
        set msgRead to read status of msg
        set msgFlagged to flagged status of msg
        set msgContent to content of msg
        {content_truncation}

        -- Get recipients
        set toList to ""
        repeat with recip in to recipients of msg
            set toList to toList & address of recip & ", "
        end repeat
        if toList is not "" then set toList to text 1 thru -3 of toList

        set ccList to ""
        repeat with recip in cc recipients of msg
            set ccList to ccList & address of recip & ", "
        end repeat
        if ccList is not "" then set ccList to text 1 thru -3 of ccList

        set output to output & msgId & (ASCII character 31) & msgSubject & (ASCII character 31) & msgSender & (ASCII character 31) & toList & (ASCII character 31) & ccList & (ASCII character 31) & msgDate & (ASCII character 31) & msgRead & (ASCII character 31) & msgFlagged & (ASCII character 31) & msgContent & (ASCII character 29)
    end repeat

    return output
end tell
'''
        else:
            # Summary only (no content)
            return f'''
tell application "Mail"
    set output to ""
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc

    set msgList to (messages of mb {filter_condition})
    set totalCount to count of msgList
    set startIdx to {offset} + 1
    set endIdx to {offset} + {limit}
    if endIdx > totalCount then set endIdx to totalCount
    if startIdx > totalCount then set startIdx to totalCount + 1

    -- Output total count as first line
    set output to "TOTAL:" & totalCount & linefeed

    repeat with i from startIdx to endIdx
        set msg to item i of msgList
        set msgId to id of msg
        set msgSubject to subject of msg
        set msgSender to sender of msg
        set msgDate to date received of msg as string
        set msgRead to read status of msg
        set msgFlagged to flagged status of msg
        set output to output & msgId & (ASCII character 30) & msgSubject & (ASCII character 30) & msgSender & (ASCII character 30) & msgDate & (ASCII character 30) & msgRead & (ASCII character 30) & msgFlagged & linefeed
    end repeat

    return output
end tell
'''

    @staticmethod
    def read_message(account_name: str, mailbox_path: str, message_id: int) -> str:
        """Read full message content by ID."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set msg to first message of mb whose id is {message_id}

    set msgId to id of msg
    set msgSubject to subject of msg
    set msgSender to sender of msg
    set msgDate to date received of msg as string
    set msgRead to read status of msg
    set msgFlagged to flagged status of msg
    set msgContent to content of msg

    -- Get recipients
    set toList to ""
    repeat with recip in to recipients of msg
        set toList to toList & address of recip & ", "
    end repeat
    if toList is not "" then set toList to text 1 thru -3 of toList

    set ccList to ""
    repeat with recip in cc recipients of msg
        set ccList to ccList & address of recip & ", "
    end repeat
    if ccList is not "" then set ccList to text 1 thru -3 of ccList

    return msgId & (ASCII character 31) & msgSubject & (ASCII character 31) & msgSender & (ASCII character 31) & toList & (ASCII character 31) & ccList & (ASCII character 31) & msgDate & (ASCII character 31) & msgRead & (ASCII character 31) & msgFlagged & (ASCII character 31) & msgContent
end tell
'''

    @staticmethod
    def move_message(
        account_name: str,
        mailbox_path: str,
        message_id: int,
        destination_mailbox: str,
        is_gmail: bool = False,
    ) -> str:
        """Move a message to another mailbox.

        For Gmail/IMAP accounts, a simple 'move' only adds the destination label
        but doesn't remove the source label (INBOX). We use move + archive:
        1. Move to destination (adds the label)
        2. Move from source to All Mail (archives - removes INBOX label)

        For non-Gmail accounts, we use a simple move.

        Args:
            account_name: Name of the mail account
            mailbox_path: Source mailbox path
            message_id: ID of message to move
            destination_mailbox: Destination mailbox path
            is_gmail: Whether this is a Gmail account (enables archive workaround)
        """
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        destination_mailbox = esc(destination_mailbox)

        if is_gmail:
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set srcMb to mailbox "{mailbox_path}" of acc
    set destMb to mailbox "{destination_mailbox}" of acc
    set msg to first message of srcMb whose id is {message_id}

    -- Try to find Archive mailbox for Gmail archive behavior
    set archiveMb to missing value
    try
        set archiveMb to mailbox "Archive" of acc
    end try
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Archiv" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Archivo" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "[Gmail]/All Mail" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "[Gmail]/Todos" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Alle Nachrichten" of acc
        end try
    end if

    -- Store message id (RFC 822 Message-ID) for reliable lookup after move
    set msgMessageId to message id of msg

    -- For Gmail: first archive (move to Archive) to remove INBOX label
    -- Then move from Archive to destination
    if archiveMb is not missing value then
        -- Step 1: Archive the message (removes INBOX label)
        move msg to archiveMb

        -- Step 2: Find in Archive and move to destination with recovery
        try
            set archivedMsg to first message of archiveMb whose message id is msgMessageId
            move archivedMsg to destMb

            -- Find the message in destination
            set movedMsg to first message of destMb whose message id is msgMessageId
            set newId to id of movedMsg
        on error errMsg
            -- Recovery: move back to source if second move fails
            try
                set recoveredMsg to first message of archiveMb whose message id is msgMessageId
                move recoveredMsg to srcMb
            end try
            error "Move failed, message restored to source: " & errMsg
        end try
    else
        -- No Archive mailbox, use simple move (may leave in INBOX for Gmail)
        move msg to destMb
        set movedMsg to first message of destMb whose message id is msgMessageId
        set newId to id of movedMsg
    end if

    return "moved" & (ASCII character 30) & newId
end tell
'''
        else:
            # Non-Gmail: simple move
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set srcMb to mailbox "{mailbox_path}" of acc
    set destMb to mailbox "{destination_mailbox}" of acc
    set msg to first message of srcMb whose id is {message_id}

    -- Store message id (RFC 822 Message-ID) for reliable lookup after move
    set msgMessageId to message id of msg

    -- Simple move for non-Gmail accounts
    move msg to destMb
    set movedMsg to first message of destMb whose message id is msgMessageId
    set newId to id of movedMsg

    return "moved" & (ASCII character 30) & newId
end tell
'''

    @staticmethod
    def set_read_status(
        account_name: str, mailbox_path: str, message_id: int, read: bool
    ) -> str:
        """Set the read status of a message."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        read_val = "true" if read else "false"
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set msg to first message of mb whose id is {message_id}
    set read status of msg to {read_val}
    return "done"
end tell
'''

    @staticmethod
    def set_flagged_status(
        account_name: str, mailbox_path: str, message_id: int, flagged: bool
    ) -> str:
        """Set the flagged status of a message."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        flagged_val = "true" if flagged else "false"
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set msg to first message of mb whose id is {message_id}
    set flagged status of msg to {flagged_val}
    return "done"
end tell
'''

    @staticmethod
    def get_account_server(account_name: str) -> str:
        """Get the server name for an account (used for Gmail detection)."""
        account_name = esc(account_name)
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    try
        set serverName to server name of acc
        return serverName
    on error
        return ""
    end try
end tell
'''

    @staticmethod
    def read_messages(account_name: str, mailbox_path: str, message_ids: list[int]) -> str:
        """Read multiple messages by their IDs in a single call."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        ids_str = ", ".join(str(mid) for mid in message_ids)
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set idList to {{{ids_str}}}
    set output to ""

    repeat with msgId in idList
        try
            set msg to first message of mb whose id is msgId

            set msgSubject to subject of msg
            set msgSender to sender of msg
            set msgDate to date received of msg as string
            set msgRead to read status of msg
            set msgFlagged to flagged status of msg
            set msgContent to content of msg

            -- Get recipients
            set toList to ""
            repeat with recip in to recipients of msg
                set toList to toList & address of recip & ", "
            end repeat
            if toList is not "" then set toList to text 1 thru -3 of toList

            set ccList to ""
            repeat with recip in cc recipients of msg
                set ccList to ccList & address of recip & ", "
            end repeat
            if ccList is not "" then set ccList to text 1 thru -3 of ccList

            set output to output & msgId & (ASCII character 31) & msgSubject & (ASCII character 31) & msgSender & (ASCII character 31) & toList & (ASCII character 31) & ccList & (ASCII character 31) & msgDate & (ASCII character 31) & msgRead & (ASCII character 31) & msgFlagged & (ASCII character 31) & msgContent & (ASCII character 29)
        on error errMsg
            set output to output & msgId & (ASCII character 31) & "ERROR" & (ASCII character 31) & errMsg & (ASCII character 29)
        end try
    end repeat

    return output
end tell
'''

    @staticmethod
    def search_messages(
        account_name: str,
        mailbox_path: str,
        sender_contains: str | None = None,
        subject_contains: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> str:
        """Search messages by sender and/or subject."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)

        # Build filter conditions - escape search terms for AppleScript
        conditions = []
        if sender_contains:
            conditions.append(f'sender contains "{esc(sender_contains)}"')
        if subject_contains:
            conditions.append(f'subject contains "{esc(subject_contains)}"')

        if conditions:
            filter_clause = "whose " + " and ".join(conditions)
        else:
            filter_clause = ""

        return f'''
tell application "Mail"
    set output to ""
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc

    set msgList to (messages of mb {filter_clause})
    set totalCount to count of msgList
    set startIdx to {offset} + 1
    set endIdx to {offset} + {limit}
    if endIdx > totalCount then set endIdx to totalCount
    if startIdx > totalCount then set startIdx to totalCount + 1

    -- Output total count as first line
    set output to "TOTAL:" & totalCount & linefeed

    repeat with i from startIdx to endIdx
        set msg to item i of msgList
        set msgId to id of msg
        set msgSubject to subject of msg
        set msgSender to sender of msg
        set msgDate to date received of msg as string
        set msgRead to read status of msg
        set msgFlagged to flagged status of msg
        set output to output & msgId & (ASCII character 30) & msgSubject & (ASCII character 30) & msgSender & (ASCII character 30) & msgDate & (ASCII character 30) & msgRead & (ASCII character 30) & msgFlagged & linefeed
    end repeat

    return output
end tell
'''

    @staticmethod
    def bulk_move_messages(
        account_name: str,
        mailbox_path: str,
        message_ids: list[int],
        destination_mailbox: str,
        is_gmail: bool = False,
    ) -> str:
        """Move multiple messages to another mailbox.

        For Gmail/IMAP accounts, a simple 'move' only adds the destination label
        but doesn't remove the source label (INBOX). We use move + archive:
        1. Move to destination (adds the label)
        2. Move from source to All Mail (archives - removes INBOX label)

        For non-Gmail accounts, we use a simple move.
        """
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        destination_mailbox = esc(destination_mailbox)
        ids_str = ", ".join(str(mid) for mid in message_ids)

        if is_gmail:
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set srcMb to mailbox "{mailbox_path}" of acc
    set destMb to mailbox "{destination_mailbox}" of acc
    set idList to {{{ids_str}}}
    set output to ""

    -- Try to find Archive mailbox for Gmail archive behavior
    set archiveMb to missing value
    try
        set archiveMb to mailbox "Archive" of acc
    end try
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Archiv" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Archivo" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "[Gmail]/All Mail" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "[Gmail]/Todos" of acc
        end try
    end if
    if archiveMb is missing value then
        try
            set archiveMb to mailbox "Alle Nachrichten" of acc
        end try
    end if

    repeat with msgId in idList
        try
            set msg to first message of srcMb whose id is msgId

            -- Store message id (RFC 822 Message-ID) for reliable lookup after move
            set msgMessageId to message id of msg

            -- For Gmail: first archive (move to Archive) to remove INBOX label
            -- Then move from Archive to destination
            if archiveMb is not missing value then
                -- Step 1: Archive the message (removes INBOX label)
                move msg to archiveMb

                -- Step 2: Find in Archive and move to destination with recovery
                try
                    set archivedMsg to first message of archiveMb whose message id is msgMessageId
                    move archivedMsg to destMb

                    -- Find the message in destination
                    set movedMsg to first message of destMb whose message id is msgMessageId
                    set newId to id of movedMsg
                    set output to output & msgId & (ASCII character 30) & newId & (ASCII character 30) & "success" & linefeed
                on error errMsg
                    -- Recovery: move back to source if second move fails
                    try
                        set recoveredMsg to first message of archiveMb whose message id is msgMessageId
                        move recoveredMsg to srcMb
                        set output to output & msgId & (ASCII character 30) & msgId & (ASCII character 30) & "error:recovered - " & errMsg & linefeed
                    on error
                        set output to output & msgId & (ASCII character 30) & msgId & (ASCII character 30) & "error:stranded in archive - " & errMsg & linefeed
                    end try
                end try
            else
                -- No Archive mailbox, use simple move (may leave in INBOX for Gmail)
                move msg to destMb
                set movedMsg to first message of destMb whose message id is msgMessageId
                set newId to id of movedMsg
                set output to output & msgId & (ASCII character 30) & newId & (ASCII character 30) & "success" & linefeed
            end if
        on error errMsg
            set output to output & msgId & (ASCII character 30) & msgId & (ASCII character 30) & "error:" & errMsg & linefeed
        end try
    end repeat

    return output
end tell
'''
        else:
            # Non-Gmail: simple move
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set srcMb to mailbox "{mailbox_path}" of acc
    set destMb to mailbox "{destination_mailbox}" of acc
    set idList to {{{ids_str}}}
    set output to ""

    repeat with msgId in idList
        try
            set msg to first message of srcMb whose id is msgId

            -- Store message id (RFC 822 Message-ID) for reliable lookup after move
            set msgMessageId to message id of msg

            -- Simple move for non-Gmail accounts
            move msg to destMb
            set movedMsg to first message of destMb whose message id is msgMessageId
            set newId to id of movedMsg

            set output to output & msgId & (ASCII character 30) & newId & (ASCII character 30) & "success" & linefeed
        on error errMsg
            set output to output & msgId & (ASCII character 30) & msgId & (ASCII character 30) & "error:" & errMsg & linefeed
        end try
    end repeat

    return output
end tell
'''

    @staticmethod
    def bulk_set_read_status(
        account_name: str,
        mailbox_path: str,
        message_ids: list[int],
        read: bool,
    ) -> str:
        """Set read status for multiple messages."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        ids_str = ", ".join(str(mid) for mid in message_ids)
        read_val = "true" if read else "false"
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set idList to {{{ids_str}}}
    set successCount to 0

    repeat with msgId in idList
        try
            set msg to first message of mb whose id is msgId
            set read status of msg to {read_val}
            set successCount to successCount + 1
        end try
    end repeat

    return successCount & " of " & (count of idList) & " messages updated"
end tell
'''

    @staticmethod
    def bulk_set_flagged_status(
        account_name: str,
        mailbox_path: str,
        message_ids: list[int],
        flagged: bool,
    ) -> str:
        """Set flagged status for multiple messages."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        ids_str = ", ".join(str(mid) for mid in message_ids)
        flagged_val = "true" if flagged else "false"
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set idList to {{{ids_str}}}
    set successCount to 0

    repeat with msgId in idList
        try
            set msg to first message of mb whose id is msgId
            set flagged status of msg to {flagged_val}
            set successCount to successCount + 1
        end try
    end repeat

    return successCount & " of " & (count of idList) & " messages updated"
end tell
'''

    @staticmethod
    def create_mailbox(account_name: str, mailbox_name: str, parent_mailbox: str | None = None) -> str:
        """Create a new mailbox in an account."""
        account_name = esc(account_name)
        mailbox_name = esc(mailbox_name)
        if parent_mailbox:
            parent_mailbox = esc(parent_mailbox)
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set parentMb to mailbox "{parent_mailbox}" of acc
    make new mailbox with properties {{name:"{mailbox_name}"}} at parentMb
    return "created"
end tell
'''
        else:
            return f'''
tell application "Mail"
    set acc to account "{account_name}"
    make new mailbox with properties {{name:"{mailbox_name}"}} at acc
    return "created"
end tell
'''

    @staticmethod
    def rename_mailbox(account_name: str, mailbox_path: str, new_name: str) -> str:
        """Rename a mailbox."""
        account_name = esc(account_name)
        mailbox_path = esc(mailbox_path)
        new_name = esc(new_name)
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set name of mb to "{new_name}"
    return "renamed"
end tell
'''
