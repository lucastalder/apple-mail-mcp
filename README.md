# Apple Mail MCP

An MCP (Model Context Protocol) server for Apple Mail, enabling AI assistants to read, search, and organize emails.

## Features

- List mail accounts and mailboxes
- Create and rename mailboxes
- Search messages by sender or subject
- Read message content (single or batch)
- Move messages between mailboxes
- Set read/flagged status
- All operations support batch processing for efficiency

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/apple-mail-mcp.git
cd apple-mail-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

## Configuration

Add to your Claude Code MCP settings (`~/.claude.json` or project settings):

```json
{
  "mcpServers": {
    "apple-mail": {
      "type": "stdio",
      "command": "/path/to/apple-mail-mcp/.venv/bin/python",
      "args": ["-m", "apple_mail_mcp.server"]
    }
  }
}
```

## Tools

### list_accounts
List all mail accounts configured in Apple Mail.

### list_mailboxes
List mailboxes (folders) for a specific account.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name as shown in Mail.app |
| include_nested | bool | Include nested mailboxes (default: true) |

### list_messages
List messages in a mailbox with optional filtering.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Path to mailbox (e.g., "INBOX") |
| limit | int | Max messages to return (default: 50) |
| unread_only | bool | Only unread messages (default: false) |
| flagged_only | bool | Only flagged messages (default: false) |

### search_messages
Search messages by sender and/or subject.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Path to mailbox |
| sender_contains | string | Filter by sender (optional) |
| subject_contains | string | Filter by subject (optional) |
| limit | int | Max messages to return (default: 50) |

### read_messages
Read full content of one or more messages.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Path to mailbox |
| message_ids | list[int] | List of message IDs to read |

### move_messages
Move one or more messages to another mailbox.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Source mailbox path |
| message_ids | list[int] | List of message IDs to move |
| destination_mailbox | string | Destination mailbox path |

Returns the new message IDs (IDs change after moving).

### set_messages_status
Set read and/or flagged status for one or more messages.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Path to mailbox |
| message_ids | list[int] | List of message IDs to update |
| read_status | bool | Mark as read (true) or unread (false) |
| flagged_status | bool | Flag (true) or unflag (false) |

### create_mailbox
Create a new mailbox (folder).

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_name | string | Name for the new mailbox |
| parent_mailbox | string | Parent mailbox path for nested creation (optional) |

### rename_mailbox
Rename a mailbox.

| Parameter | Type | Description |
|-----------|------|-------------|
| account_name | string | The account name |
| mailbox_path | string | Path to the mailbox to rename |
| new_name | string | New name for the mailbox |

## Examples

### Search and archive newsletters
```
1. search_messages(account="Work", mailbox="INBOX", sender_contains="newsletter")
2. move_messages(account="Work", mailbox="INBOX", message_ids=[...], destination="Archive")
```

### Mark all messages from a sender as read
```
1. search_messages(account="Personal", mailbox="INBOX", sender_contains="notifications@")
2. set_messages_status(account="Personal", mailbox="INBOX", message_ids=[...], read_status=true)
```

### Read recent unread messages
```
1. list_messages(account="Work", mailbox="INBOX", limit=10, unread_only=true)
2. read_messages(account="Work", mailbox="INBOX", message_ids=[...])
```

## Requirements

- macOS with Apple Mail configured
- Python 3.10+
- Mail.app must be running for AppleScript access

## License

MIT
