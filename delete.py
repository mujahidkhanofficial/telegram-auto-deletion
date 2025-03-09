#!/usr/bin/env python3
"""
Comprehensive Telegram Deletion Tool
This script allows you to delete all conversations from your Telegram account,
including private chats, groups, and channels.
"""

import os
import sys
import asyncio
import logging
from getpass import getpass
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Import our local imghdr module for Python 3.13 compatibility
import imghdr

try:
    from telethon import TelegramClient, errors
    from telethon.tl.types import Channel, Chat, User, Dialog
    from telethon.tl.functions.channels import LeaveChannelRequest
    from telethon.tl.functions.messages import DeleteChatUserRequest, DeleteHistoryRequest
except ImportError:
    print("Telethon library not found. Please install it using: pip install telethon")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    print("API_ID and API_HASH not found in .env file.")
    print("Please create a .env file with your Telegram API credentials.")
    print("See README.md for instructions.")
    sys.exit(1)

class TelegramItem:
    """Class to represent a Telegram conversation item (chat, group, or channel)."""
    def __init__(self, id: int, name: str, type: str, entity: any):
        self.id = id
        self.name = name
        self.type = type
        self.entity = entity
        self.selected = False  # Default to not selected

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"

async def get_all_items(client: TelegramClient) -> Dict[str, List[TelegramItem]]:
    """
    Get all conversations the user has.
    
    Args:
        client: The Telegram client instance
        
    Returns:
        A dictionary with categories as keys and lists of TelegramItem objects as values
    """
    items = {
        "private_chats": [],
        "groups": [],
        "channels": [],
        "other": []
    }
    
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        
        if isinstance(entity, User):
            # This is a private chat
            items["private_chats"].append(
                TelegramItem(
                    entity.id,
                    f"{entity.first_name} {entity.last_name if entity.last_name else ''} (@{entity.username if entity.username else 'No username'})",
                    "Private Chat",
                    entity
                )
            )
        elif isinstance(entity, Channel):
            if entity.broadcast:
                # This is a broadcast channel
                items["channels"].append(
                    TelegramItem(
                        entity.id,
                        dialog.name,
                        "Broadcast Channel",
                        entity
                    )
                )
            elif entity.megagroup:
                # This is a supergroup
                items["groups"].append(
                    TelegramItem(
                        entity.id,
                        dialog.name,
                        "Supergroup",
                        entity
                    )
                )
            else:
                # This is a regular channel
                items["channels"].append(
                    TelegramItem(
                        entity.id,
                        dialog.name,
                        "Channel",
                        entity
                    )
                )
        elif isinstance(entity, Chat):
            # This is a small group
            items["groups"].append(
                TelegramItem(
                    entity.id,
                    dialog.name,
                    "Small Group",
                    entity
                )
            )
        else:
            # Other types
            items["other"].append(
                TelegramItem(
                    getattr(entity, 'id', 0),
                    dialog.name,
                    "Other",
                    entity
                )
            )
    
    return items

async def delete_private_chat(client: TelegramClient, item: TelegramItem) -> bool:
    """
    Delete a private chat history.
    
    Args:
        client: The Telegram client instance
        item: The TelegramItem object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Delete the chat history
        await client(DeleteHistoryRequest(
            peer=item.entity,
            max_id=0,  # Delete all messages
            just_clear=False,  # Delete for both sides
            revoke=True  # Revoke messages
        ))
        return True
    except errors.FloodWaitError as e:
        logger.error(f"Rate limited. Please wait {e.seconds} seconds before trying again.")
        return False
    except Exception as e:
        logger.error(f"Error deleting chat with {item.name} (ID: {item.id}): {str(e)}")
        return False

async def leave_group_or_channel(client: TelegramClient, item: TelegramItem) -> bool:
    """
    Leave a group or channel.
    
    Args:
        client: The Telegram client instance
        item: The TelegramItem object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if isinstance(item.entity, Channel):
            # For channels and supergroups
            await client(LeaveChannelRequest(item.entity))
        else:
            # For regular groups
            await client(DeleteChatUserRequest(
                chat_id=item.id,
                user_id='me'
            ))
        return True
    except errors.FloodWaitError as e:
        logger.error(f"Rate limited. Please wait {e.seconds} seconds before trying again.")
        return False
    except Exception as e:
        logger.error(f"Error leaving {item.type} {item.name} (ID: {item.id}): {str(e)}")
        return False

async def delete_item(client: TelegramClient, item: TelegramItem) -> bool:
    """
    Delete or leave a Telegram item based on its type.
    
    Args:
        client: The Telegram client instance
        item: The TelegramItem object
        
    Returns:
        True if successful, False otherwise
    """
    if item.type == "Private Chat":
        return await delete_private_chat(client, item)
    elif "Group" in item.type or "Channel" in item.type:
        return await leave_group_or_channel(client, item)
    else:
        logger.warning(f"Unknown item type: {item.type}. Skipping {item.name}.")
        return False

async def interactive_selection(all_items: Dict[str, List[TelegramItem]]) -> List[TelegramItem]:
    """
    Allow user to interactively select which items to delete.
    
    Args:
        all_items: Dictionary with categories as keys and lists of TelegramItem objects as values
        
    Returns:
        List of selected TelegramItem objects
    """
    # Flatten all items for display
    flat_items = []
    for category, items in all_items.items():
        flat_items.extend(items)
    
    # Display items
    print("\nSelect items to delete/leave:")
    for i, item in enumerate(flat_items, 1):
        selected = "[X]" if item.selected else "[ ]"
        print(f"{i}. {selected} {item}")
    
    while True:
        print("\nCommands:")
        print("  number       - Toggle selection of a specific item (e.g., '5')")
        print("  range        - Toggle a range of items (e.g., '5-10')")
        print("  all          - Select all items")
        print("  none         - Deselect all items")
        print("  chats        - Select all private chats")
        print("  groups       - Select all groups")
        print("  channels     - Select all channels")
        print("  done         - Proceed with the selected items")
        print("  quit         - Exit without making changes")
        
        cmd = input("\nEnter command: ").strip().lower()
        
        if cmd == "done":
            selected_items = [item for item in flat_items if item.selected]
            if not selected_items:
                print("No items selected. Please select at least one item or type 'quit'.")
                continue
            return selected_items
        
        elif cmd == "quit":
            print("Operation cancelled.")
            sys.exit(0)
        
        elif cmd == "all":
            for item in flat_items:
                item.selected = True
            print("All items selected.")
        
        elif cmd == "none":
            for item in flat_items:
                item.selected = False
            print("All items deselected.")
        
        elif cmd == "chats":
            for item in flat_items:
                if item.type == "Private Chat":
                    item.selected = True
            print("All private chats selected.")
        
        elif cmd == "groups":
            for item in flat_items:
                if "Group" in item.type:
                    item.selected = True
            print("All groups selected.")
        
        elif cmd == "channels":
            for item in flat_items:
                if "Channel" in item.type:
                    item.selected = True
            print("All channels selected.")
        
        elif "-" in cmd:
            try:
                start, end = map(int, cmd.split("-"))
                if 1 <= start <= len(flat_items) and 1 <= end <= len(flat_items):
                    for i in range(start-1, end):
                        flat_items[i].selected = not flat_items[i].selected
                    print(f"Toggled selection for items {start} to {end}.")
                else:
                    print(f"Invalid range. Please use numbers between 1 and {len(flat_items)}.")
            except ValueError:
                print("Invalid range format. Use 'start-end' (e.g., '5-10').")
        
        elif cmd.isdigit():
            idx = int(cmd)
            if 1 <= idx <= len(flat_items):
                flat_items[idx-1].selected = not flat_items[idx-1].selected
                selected = "Selected" if flat_items[idx-1].selected else "Deselected"
                print(f"{selected} item: {flat_items[idx-1].name}")
            else:
                print(f"Invalid item number. Please use a number between 1 and {len(flat_items)}.")
        
        else:
            print("Unknown command. Please try again.")
        
        # Display current selection status
        selected_count = sum(1 for item in flat_items if item.selected)
        print(f"\nCurrently selected: {selected_count} out of {len(flat_items)} items")

async def main():
    """Main function to run the script."""
    print("Comprehensive Telegram Deletion Tool")
    print("-----------------------------------")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Delete Telegram conversations")
    parser.add_argument("--all", action="store_true", help="Delete all conversations without confirmation")
    parser.add_argument("--chats", action="store_true", help="Delete all private chats")
    parser.add_argument("--groups", action="store_true", help="Delete all groups")
    parser.add_argument("--channels", action="store_true", help="Delete all channels")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between deletions (in seconds)")
    parser.add_argument("--interactive", action="store_true", help="Use interactive selection mode")
    args = parser.parse_args()
    
    # Get phone number
    phone = input("Enter your phone number (with country code, e.g., +1234567890): ")
    
    # Create the client
    client = TelegramClient("telegram_delete_session", API_ID, API_HASH)
    
    try:
        # Start the client
        await client.start(phone=phone, password=lambda: getpass("Enter your 2FA password (if any): "))
        
        if not await client.is_user_authorized():
            print("Authentication failed. Please try again.")
            return
        
        # Get user info
        me = await client.get_me()
        print(f"\nLogged in as: {me.first_name} {me.last_name if me.last_name else ''} (@{me.username if me.username else 'No username'})")
        
        # Get all conversations
        print("\nFetching all conversations... This may take a moment.")
        all_items = await get_all_items(client)
        
        # Count items by category
        counts = {category: len(items) for category, items in all_items.items()}
        total_count = sum(counts.values())
        
        if total_count == 0:
            print("No conversations found.")
            return
        
        print(f"\nFound {total_count} total conversations:")
        print(f"- Private Chats: {counts['private_chats']}")
        print(f"- Groups: {counts['groups']}")
        print(f"- Channels: {counts['channels']}")
        print(f"- Other: {counts['other']}")
        
        # Determine which items to delete based on command line arguments
        items_to_delete = []
        
        if args.interactive:
            # Interactive selection mode
            items_to_delete = await interactive_selection(all_items)
        else:
            # Command line selection mode
            if args.all:
                # Select all items
                for category, items in all_items.items():
                    items_to_delete.extend(items)
            else:
                # Select specific categories
                if args.chats:
                    items_to_delete.extend(all_items["private_chats"])
                if args.groups:
                    items_to_delete.extend(all_items["groups"])
                if args.channels:
                    items_to_delete.extend(all_items["channels"])
                
                # If no specific category was selected, ask the user what to delete
                if not (args.chats or args.groups or args.channels):
                    print("\nWhat would you like to delete?")
                    print("1. All conversations")
                    print("2. Private chats only")
                    print("3. Groups only")
                    print("4. Channels only")
                    print("5. Interactive selection")
                    print("6. Cancel")
                    
                    choice = input("\nEnter your choice (1-6): ").strip()
                    
                    if choice == "1":
                        for category, items in all_items.items():
                            items_to_delete.extend(items)
                    elif choice == "2":
                        items_to_delete.extend(all_items["private_chats"])
                    elif choice == "3":
                        items_to_delete.extend(all_items["groups"])
                    elif choice == "4":
                        items_to_delete.extend(all_items["channels"])
                    elif choice == "5":
                        items_to_delete = await interactive_selection(all_items)
                    elif choice == "6":
                        print("Operation cancelled.")
                        return
                    else:
                        print("Invalid choice. Operation cancelled.")
                        return
        
        # Confirm deletion
        if not items_to_delete:
            print("No items selected for deletion. Exiting.")
            return
        
        # Count by type for confirmation
        type_counts = {}
        for item in items_to_delete:
            type_counts[item.type] = type_counts.get(item.type, 0) + 1
        
        print(f"\nYou are about to delete/leave {len(items_to_delete)} conversations:")
        for type_name, count in type_counts.items():
            print(f"- {type_name}: {count}")
        
        confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower()
        
        if confirm != "yes":
            print("Operation cancelled.")
            return
        
        # Delete/leave items
        print("\nProcessing... This may take some time.")
        success_count = 0
        
        for i, item in enumerate(items_to_delete, 1):
            print(f"Processing {i}/{len(items_to_delete)}: {item.name} ({item.type})...", end="", flush=True)
            success = await delete_item(client, item)
            
            if success:
                print(" Done")
                success_count += 1
            else:
                print(" Failed")
            
            # Add a delay to avoid rate limiting
            if i < len(items_to_delete):  # Don't delay after the last item
                await asyncio.sleep(args.delay)
        
        print(f"\nOperation completed. Successfully processed {success_count} out of {len(items_to_delete)} items.")
        
    except errors.PhoneNumberInvalidError:
        print("Invalid phone number. Please make sure to include the country code.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 