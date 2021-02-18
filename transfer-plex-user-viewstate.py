import argparse
import sqlite3
import sys

from tabulate import tabulate


def get_valid_input(prompt: str, valid_values: list, invalid_msg: str) -> str:
    input_value = None
    input_valid = False
    while not input_valid:
        input_value = input(f'{prompt} ')
        input_valid = input_value in valid_values
        if not input_valid:
            print(invalid_msg)

    return input_value


def str_range(stop: int) -> list:
    values = list(range(stop))
    return [str(v) for v in values]


parser = argparse.ArgumentParser(description='Transfer Plex user viewstate and play history between users')
parser.add_argument('-p', '--db-path', help='Path to com.plexapp.plugins.library.db file', type=str, required=True)
args = parser.parse_args()

connection = sqlite3.connect(args.db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

# Get users
cursor.execute('SELECT id, name, created_at FROM accounts WHERE id > 0')
accounts = cursor.fetchall()

# Print users
print(tabulate([{'index': i, 'name': accounts[i]['name']} for i in range(0, len(accounts))], headers='keys'))

# Ask user to select source user
sourceAccountIndex = int(get_valid_input(
    'First, please enter the _source_ account index',
    str_range(len(accounts)),
    'No account with that ID, please enter a valid account index'
))

# Ask user to select target user
targetAccountIndex = int(get_valid_input(
    'Now, please enter the _target_ account index',
    str_range(len(accounts)),
    'No account with that ID, please enter a valid account index'
))

# Ask user to select copying/moving view state
mode = get_valid_input(
    'Do you want to copy or move the viewstate? ([c]opy/[m]move)',
    ['c', 'copy', 'm', 'move'],
    'Please select either [c]opy or [m]ove'
)

# Get source account viewstate
sql = 'SELECT guid, rating, view_offset, view_count, last_viewed_at, created_at, updated_at, skip_count, ' \
      'last_skipped_at, changed_at, extra_data, last_rated_at FROM metadata_item_settings ' \
      'WHERE account_id = :account_id'
cursor.execute(sql, {'account_id': accounts[sourceAccountIndex]['id']})
sourceViewstate = cursor.fetchall()

# Get source account play history
sql = 'SELECT guid, metadata_type, library_section_id, grandparent_title, parent_index, parent_title, ' \
      '"index", title, thumb_url, viewed_at, grandparent_guid, originally_available_at, device_id ' \
      'FROM metadata_item_views WHERE account_id = :account_id'
cursor.execute(sql, {'account_id': accounts[sourceAccountIndex]['id']})
sourcePlayHistory = cursor.fetchall()

# Make sure source account has any viewstate items
if len(sourceViewstate) == 0 and len(sourcePlayHistory) == 0:
    sys.exit('Source account has no viewstate/play history items')

# Check for existing viewstate items of target user
sql = 'SELECT id, guid FROM metadata_item_settings WHERE account_id = :account_id'
cursor.execute(sql, {'account_id': accounts[targetAccountIndex]['id']})
targetViewstate = cursor.fetchall()

# Check for existing play history items of target user
sql = 'SELECT id, guid FROM metadata_item_views WHERE account_id = :account_id'
cursor.execute(sql, {'account_id': accounts[targetAccountIndex]['id']})
targetPlayHistory = cursor.fetchall()

# Handle existing target account viewstates items if any were found
if len(targetViewstate) > 0 or len(targetPlayHistory):
    print(f'Found existing viewstate ({len(targetViewstate)} items)/play history ({len(targetPlayHistory)} items) '
          f'for target account')
    handleExisting = get_valid_input(
        'Do you want to add to or replace existing viewstate/play history? ([a]dd/[r]eplace)',
        ['a', 'add', 'r', 'replace'],
        'Please select either [a]dd/[r]eplace'
    )

    if handleExisting in ['a', 'add']:
        # Remove source account's viewstate for any media items for which target user has an existing viewstate
        sourceViewstateGuids = [e['guid'] for e in sourceViewstate]
        viewstateGuidsToDelete = [e['guid'] for e in targetViewstate if e['guid'] in sourceViewstateGuids]
        for guid in viewstateGuidsToDelete:
            # Get index of media item
            # (indexes are the same between guid list and overall source viewstate list,
            # so we can use the index to remove the media item's source viewstate from the copy/move list)
            index = sourceViewstateGuids.index(guid)
            # Remove viewstate for media item from copy/move list
            del sourceViewstate[index], sourceViewstateGuids[index]

            # If we are moving the viewstate, remove viewstate items we don't need to move from source user
            if mode in ['m', 'move']:
                sql = 'DELETE FROM metadata_item_settings WHERE account_id = :account_id AND guid = :guid'
                cursor.execute(sql, {'account_id': accounts[sourceAccountIndex]['id'], 'guid': guid})

        # Remove source account's play history accordingly
        sourcePlayHistoryGuids = [e['guid'] for e in sourcePlayHistory]
        # Play history may contain multiple entries for one guid (one user playing an item multiple items)
        # => make sure to get a list of unique guids
        playHistoryGuidsToDelete = list(set([e['guid'] for e in targetPlayHistory
                                             if e['guid'] in sourcePlayHistoryGuids]))
        for guid in playHistoryGuidsToDelete:
            # Delete add play history items for guid from source user list (and database, if we are moving)
            while guid in sourcePlayHistoryGuids:
                index = sourcePlayHistoryGuids.index(guid)
                del sourcePlayHistory[index], sourcePlayHistoryGuids[index]
                if mode in ['m', 'move']:
                    sql = 'DELETE FROM metadata_item_views WHERE account_id = :account_id AND guid = :guid'
                    cursor.execute(sql, {'account_id': accounts[sourceAccountIndex]['id'], 'guid': guid})
    elif handleExisting in ['r', 'replace']:
        # Remove existing viewstate items
        for entry in targetViewstate:
            sql = 'DELETE FROM metadata_item_settings WHERE id = :id'
            cursor.execute(sql, {'id': entry['id']})

        # Remove existing play history items
        for entry in targetPlayHistory:
            sql = 'DELETE FROM metadata_item_views WHERE id = :id'
            cursor.execute(sql, {'id': entry['id']})

if mode in ['c', 'copy']:
    print(f'Copying viewstate ({len(sourceViewstate)} items) and play history ({len(sourcePlayHistory)} items) '
          f'from {accounts[sourceAccountIndex]["name"]} to {accounts[targetAccountIndex]["name"]}')

    # Copy viewstate items
    sql = 'INSERT INTO metadata_item_settings (account_id, guid, rating, view_offset, view_count, last_viewed_at, ' \
          'created_at, updated_at, skip_count, last_skipped_at, changed_at, extra_data, last_rated_at) VALUES (?, ' \
          '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '
    for existingEntry in sourceViewstate:
        newEntry = {'account_id': accounts[targetAccountIndex]['id'], **existingEntry}
        cursor.execute(sql, list(newEntry.values()))

    # Copy play history items
    sql = 'INSERT INTO metadata_item_views (account_id, guid, metadata_type, library_section_id, grandparent_title, ' \
          'parent_index, parent_title, "index", title, thumb_url, viewed_at, grandparent_guid, ' \
          'originally_available_at, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    for existingEntry in sourcePlayHistory:
        newEntry = {'account_id': accounts[targetAccountIndex]['id'], **existingEntry}
        cursor.execute(sql, list(newEntry.values()))

    connection.commit()
elif mode in ['m', 'move']:
    print(f'Moving viewstate ({len(sourceViewstate)} items) and play history ({len(sourcePlayHistory)} items) '
          f'from {accounts[sourceAccountIndex]["name"]} to {accounts[targetAccountIndex]["name"]}')

    tables = ['metadata_item_settings', 'metadata_item_views']
    for table in tables:
        sql = f'UPDATE {table} SET account_id = :target_account_id WHERE account_id = :source_account_id'
        cursor.execute(sql, {
            'target_account_id': accounts[targetAccountIndex]['id'],
            'source_account_id': accounts[sourceAccountIndex]['id']
        })

    connection.commit()

cursor.close()
connection.close()
