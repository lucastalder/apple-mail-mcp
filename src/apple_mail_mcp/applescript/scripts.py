"""AppleScript templates for Apple Mail operations."""


class Scripts:
    """Collection of AppleScript templates for Mail.app interaction."""

    @staticmethod
    def list_accounts() -> str:
        """List all mail accounts with their details."""
        return '''
tell application "Mail"
    set output to ""
    repeat with acc in accounts
        set accName to name of acc
        set accEmail to email addresses of acc as string
        set accEnabled to enabled of acc
        set accType to account type of acc as string
        set output to output & accName & "|||" & accEmail & "|||" & accEnabled & "|||" & accType & linefeed
    end repeat
    return output
end tell
'''

    @staticmethod
    def list_mailboxes(account_name: str, include_nested: bool = True) -> str:
        """List mailboxes for a specific account."""
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
        set output to output & fullPath & "|||" & msgCount & "|||" & unreadCount & linefeed

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
        set output to output & mbName & "|||" & msgCount & "|||" & unreadCount & linefeed
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

        set output to output & msgId & "|||FIELD|||" & msgSubject & "|||FIELD|||" & msgSender & "|||FIELD|||" & toList & "|||FIELD|||" & ccList & "|||FIELD|||" & msgDate & "|||FIELD|||" & msgRead & "|||FIELD|||" & msgFlagged & "|||FIELD|||" & msgContent & "|||MSG|||"
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

    repeat with i from startIdx to endIdx
        set msg to item i of msgList
        set msgId to id of msg
        set msgSubject to subject of msg
        set msgSender to sender of msg
        set msgDate to date received of msg as string
        set msgRead to read status of msg
        set msgFlagged to flagged status of msg
        set output to output & msgId & "|||" & msgSubject & "|||" & msgSender & "|||" & msgDate & "|||" & msgRead & "|||" & msgFlagged & linefeed
    end repeat

    return output
end tell
'''

    @staticmethod
    def read_message(account_name: str, mailbox_path: str, message_id: int) -> str:
        """Read full message content by ID."""
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

    return msgId & "|||FIELD|||" & msgSubject & "|||FIELD|||" & msgSender & "|||FIELD|||" & toList & "|||FIELD|||" & ccList & "|||FIELD|||" & msgDate & "|||FIELD|||" & msgRead & "|||FIELD|||" & msgFlagged & "|||FIELD|||" & msgContent
end tell
'''

    @staticmethod
    def move_message(
        account_name: str,
        mailbox_path: str,
        message_id: int,
        destination_mailbox: str,
    ) -> str:
        """Move a message to another mailbox."""
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set srcMb to mailbox "{mailbox_path}" of acc
    set destMb to mailbox "{destination_mailbox}" of acc
    set msg to first message of srcMb whose id is {message_id}

    -- Store identifying info before move
    set msgSubject to subject of msg
    set msgDateReceived to date received of msg

    move msg to destMb

    -- Find the message in destination by matching subject and date
    set movedMsg to first message of destMb whose subject is msgSubject and date received is msgDateReceived
    set newId to id of movedMsg

    return "moved|||" & newId
end tell
'''

    @staticmethod
    def set_read_status(
        account_name: str, mailbox_path: str, message_id: int, read: bool
    ) -> str:
        """Set the read status of a message."""
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

            set output to output & msgId & "|||FIELD|||" & msgSubject & "|||FIELD|||" & msgSender & "|||FIELD|||" & toList & "|||FIELD|||" & ccList & "|||FIELD|||" & msgDate & "|||FIELD|||" & msgRead & "|||FIELD|||" & msgFlagged & "|||FIELD|||" & msgContent & "|||MSG|||"
        on error errMsg
            set output to output & msgId & "|||FIELD|||ERROR|||FIELD|||" & errMsg & "|||MSG|||"
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
        # Build filter conditions
        conditions = []
        if sender_contains:
            conditions.append(f'sender contains "{sender_contains}"')
        if subject_contains:
            conditions.append(f'subject contains "{subject_contains}"')

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

    repeat with i from startIdx to endIdx
        set msg to item i of msgList
        set msgId to id of msg
        set msgSubject to subject of msg
        set msgSender to sender of msg
        set msgDate to date received of msg as string
        set msgRead to read status of msg
        set msgFlagged to flagged status of msg
        set output to output & msgId & "|||" & msgSubject & "|||" & msgSender & "|||" & msgDate & "|||" & msgRead & "|||" & msgFlagged & linefeed
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
    ) -> str:
        """Move multiple messages to another mailbox."""
        ids_str = ", ".join(str(mid) for mid in message_ids)
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

            -- Store identifying info before move
            set msgSubject to subject of msg
            set msgDateReceived to date received of msg

            move msg to destMb

            -- Find the message in destination by matching subject and date
            set movedMsg to first message of destMb whose subject is msgSubject and date received is msgDateReceived
            set newId to id of movedMsg

            set output to output & msgId & "|||" & newId & "|||success" & linefeed
        on error errMsg
            set output to output & msgId & "|||" & msgId & "|||error:" & errMsg & linefeed
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
        if parent_mailbox:
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
        return f'''
tell application "Mail"
    set acc to account "{account_name}"
    set mb to mailbox "{mailbox_path}" of acc
    set name of mb to "{new_name}"
    return "renamed"
end tell
'''
