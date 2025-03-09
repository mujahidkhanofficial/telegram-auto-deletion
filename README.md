# Telegram Deletion Tool

A comprehensive command-line utility for managing your Telegram conversations by allowing you to delete private chats, leave groups, and exit channels.

## Features

- **Selective Deletion**: Choose which conversations to delete based on type (private chats, groups, or channels)
- **Interactive Mode**: Browse and select specific conversations through an interactive interface
- **Batch Operations**: Delete all conversations or specific categories at once
- **Rate Limit Protection**: Built-in delays to prevent Telegram API rate limiting
- **Secure Authentication**: Supports two-factor authentication
- **Detailed Logging**: Comprehensive logging of all operations

## Requirements

- Python 3.6+
- Telethon library
- python-dotenv

## Installation

1. Clone this repository or download the script
2. Install the required dependencies:

```bash
pip install telethon python-dotenv
```

3. Create a `.env` file in the same directory as the script with your Telegram API credentials:

```
API_ID=your_api_id
API_HASH=your_api_hash
```

## Getting API Credentials

To use this tool, you need to obtain API credentials from Telegram:

1. Visit https://my.telegram.org/auth
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application (you can fill in any details)
5. Copy the "App api_id" and "App api_hash" values to your `.env` file

## Usage

Run the script with Python:

```bash
python delete.py
```

### Command-line Options

- `--all`: Delete all conversations without confirmation
- `--chats`: Delete all private chats
- `--groups`: Delete all groups
- `--channels`: Delete all channels
- `--delay SECONDS`: Set the delay between deletions (default: 2.0 seconds)
- `--interactive`: Use interactive selection mode

### Interactive Selection Commands

When in interactive mode, you can use these commands:
- Enter a number (e.g., `5`) to toggle selection of a specific item
- Enter a range (e.g., `5-10`) to toggle a range of items
- `all`: Select all items
- `none`: Deselect all items
- `chats`: Select all private chats
- `groups`: Select all groups
- `channels`: Select all channels
- `done`: Proceed with the selected items
- `quit`: Exit without making changes

## Examples

Delete all private chats:
```bash
python delete.py --chats
```

Delete all groups and channels:
```bash
python delete.py --groups --channels
```

Use interactive selection with a 5-second delay between operations:
```bash
python delete.py --interactive --delay 5
```

## Warning

This tool permanently deletes conversations from your Telegram account. Use with caution as this action cannot be undone.

## License

This project is open source and available under the MIT License.