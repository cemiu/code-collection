# Written by cemiu, distributed under the MIT License

# Quick and dirty script to export iMessage conversations as searchable text; Without attatchments or images.
# This version supports macOS only, though Windows support should be possible with some light modifications.

# Usage:
# Create a local, unencrypted (!) backup of an iOS / iPadOS device, through Finder
# Open System Settings > Security & Privacy > Privacy > Full Disk Access > Add Terminal.app (Utilities folder)
# Download imessage_text_exporter_macos.py file, run Terminal, execute:
#      python imessage_text_exporter_macos.py
# Find conversation by searching messages contained within

# If you want the names in the conversations to be different, change the name_self and name_other variables below

# Grouping by replies is not supported
# Group chats are not supported, though support can be added with a little motivation
# Windows is not supported, though support can be added with a little motivation

import sqlite3
import sys
import os
import time
from contextlib import closing

db_file = None
handle_id = None
name_self = 'Me'
name_other = 'Other'

mac_path = os.path.expanduser('~/Library/Messages/chat.db')
ios_path = os.path.expanduser('~/Library/Application Support/MobileSync/Backup/')
obj_rep = u'\ufffc'

print_warning = lambda text: print(f'\033[93m{text}\033[0m')


def load_ios_backup_path():
    """Find the most recent iOS backup and return the path to the Messages DB."""
    try:
        recent_backup, recent_backup_date = None, 0
        for folder in os.listdir(ios_path):
            db_path = os.path.join(ios_path, folder, '3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28')
            if os.path.exists(db_path):
                folder_time = os.path.getctime(os.path.join(ios_path, folder))
                if folder_time > recent_backup_date:
                    recent_backup_date = folder_time
                    recent_backup = db_path

        if recent_backup is None:
            print_warning('No iOS backup found. Please connect your iPhone and run create a local backup.')
            sys.exit(1)

        backup_recency = (time.time() - recent_backup_date) / 60 / 60 / 24
        print(f'Using iOS backup that is {backup_recency:.0f} days old.')
        if backup_recency > 7:
            print_warning('It is recommended to create a fresh backup.')

        return recent_backup
    except PermissionError:
        print_warning('Permission to directory denied!\nTo fix: '
                      'System Settings > Security & Privacy > Privacy > Full Disk Access > Add Terminal.app')
        print('\nOr copy following file to a different location, and rerun with custom path:\n'
              '~/Library/Application Support/MobileSync/Backup/<backup-id>/3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28')
        sys.exit(1)


def select_db():
    """User selects which DB to use."""
    if len(sys.argv) == 2:
        print(f'Using custom DB path: {sys.argv[1]}')
        return sys.argv[1]
    elif len(sys.argv) < 2:
        print('1: iOS Backup (must be unencrypted)\n2: Custom path\n')
        choice = input('Enter your choice: ')
        if choice == '1': return load_ios_backup_path()
        elif choice == '2': return input('Enter custom path: ')
        else: print('Invalid option. Exiting.'); sys.exit(1)
    print_warning('Supply either no arguments or a single argument for the DB path. Current arguments:')
    print_warning('\n'.join(sys.argv[1:]))
    sys.exit(1)


def db_con(db):
    if not os.path.exists(db):
        print_warning(f'Path does not exist: {db}')
        sys.exit(1)

    try:
        return sqlite3.connect(db)
    except sqlite3.OperationalError:
        print(f'Could not open database file: {db}')
        sys.exit(1)


def get_handle_id(c, handle):
    while handle is None:
        message_match = input('Find a conversation by searching for it.\n'
                              'Capitalisation, spacing, etc are important!:\n')

        c.execute('SELECT handle_id, text FROM message WHERE text LIKE ?', (f'%{message_match}%',))
        rows = c.fetchall()
        if len(rows) == 0: print_warning(u'\nNo conversation found, try again or quit using \u2303+C.\n'); continue
        if len(rows) > 1:
            for i, row in enumerate(rows): print(f'{i}: {row[1]}')
            print_warning(f'\nFound {len(rows)} conversations, please be more specific or quit using \u2303+C.\n')
            continue

        handle = rows[0][0]
    return handle


def main():
    global db_file, handle_id, name_self, name_other
    if db_file is None: db_file = select_db()

    with db_con(db_file) as con, closing(con.cursor()) as c1, closing(con.cursor()) as c2:
        handle_id = get_handle_id(c1, handle_id)

        c1.execute(f'''
                    SELECT ROWID, text, is_from_me
                    FROM message
                    WHERE (handle_id IS {handle_id} AND cache_roomnames IS NULL)
                    ''')

        last_sender = None
        for row in c1:
            if row[2] != last_sender:
                last_sender = row[2]
                print(f'\n{name_self}:' if last_sender == 1 else f'\n{name_other}:')

            c2.execute('SELECT * FROM message_attachment_join WHERE message_id IS ?', (row[0],))
            attachment = c2.fetchone()
            if attachment:
                c2.execute('SELECT mime_type FROM attachment WHERE ROWID IS ?', (attachment[1],))
                mime_type = c2.fetchone()[0]
                print(f'\t<Attachment: {mime_type}>' if mime_type else '\t<Other attachment>')

            if row[1]:
                print(f'\t{row[1].strip().replace(obj_rep, "")}')


if __name__ == '__main__':
    main()

