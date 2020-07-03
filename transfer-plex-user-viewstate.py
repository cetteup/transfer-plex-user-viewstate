import argparse
import sqlite3
import sys

from tabulate import tabulate


def get_valid_input(prompt: str, valid_values: list, invalid_msg: str) -> str:
    input_value = None
    input_valid = False
    while not input_valid:
        input_value = input(f"{prompt} ")
        input_valid = input_value in valid_values
        if not input_valid:
            print(invalid_msg)

    return input_value


def str_range(stop: int) -> list:
    values = list(range(stop))
    return [str(v) for v in values]


parser = argparse.ArgumentParser("Transfer Plex user viewstate between users")
parser.add_argument("-p", "--db-path", help="Path to com.plexapp.plugins.library.db file")
args = parser.parse_args()

connection = sqlite3.connect(args.db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

# Get users
cursor.execute("SELECT id, name, created_at FROM accounts WHERE id > 0")
accounts = cursor.fetchall()

# Print users
print(tabulate([{"index": i, "name": accounts[i]["name"]} for i in range(0, len(accounts))], headers="keys"))

# Ask user to select source user
sourceAccountIndex = int(get_valid_input(
    "First, please enter the _source_ account index",
    str_range(len(accounts)),
    "No account with that ID, please enter a valid account index"
))

# Ask user to select target user
targetAccountIndex = int(get_valid_input(
    "Now, please enter the _target_ account index",
    str_range(len(accounts)),
    "No account with that ID, please enter a valid account index"
))

# Ask user to select copying/moving view state
mode = get_valid_input(
    "Do you want to copy or move the viewstate? ([c]opy/[m]move)",
    ["c", "copy", "m", "move"],
    "Please select either [c]opy or [m]ove"
)

# Get source account viewstate
sql = "SELECT * FROM metadata_item_settings WHERE account_id = :account_id"
cursor.execute(sql, {"account_id": accounts[sourceAccountIndex]["id"]})
sourceViewstate = cursor.fetchall()

# Make sure source account has any viewstate items
if len(sourceViewstate) == 0:
    sys.exit("Source account has no viewstate items")

# Check for existing viewstate items of target user
sql = "SELECT id, guid FROM metadata_item_settings WHERE account_id = :account_id"
cursor.execute(sql, {"account_id": accounts[targetAccountIndex]['id']})
targetViewstate = cursor.fetchall()

# Handle existing target account viewstates items if any were found
if len(targetViewstate) > 0:
    print(f"Found {len(targetViewstate)} existing viewstate items for target account")
    handleExisting = get_valid_input(
        "Do you want to add to or replace existing viewstate? ([a]dd/[r]eplace)",
        ["a", "add", "r", "replace"],
        "Please select either [a]dd/[r]eplace"
    )

    if handleExisting in ["a", "add"]:
        # Remove source account's viewstate for any media items for which target user has an existing viewstate
        sourceViewstateGuids = [e["guid"] for e in sourceViewstate]
        targetViewstateGuids = [e["guid"] for e in targetViewstate]
        for guid in targetViewstateGuids:
            # Check if guid is also present in source viewstate
            if guid in sourceViewstateGuids:
                # Get index of media item
                # (indexes are the same between guid list and overall source viewstate list,
                # so we can use the index to remove the media item's source viewstate from the copy/move list)
                index = sourceViewstateGuids.index(guid)
                # Remove viewstate for media item from copy/move list
                del sourceViewstate[index], sourceViewstateGuids[index]

                # If we are moving the viewstate, remove viewstate items we don't need to move from source user
                sql = "DELETE FROM metadata_item_settings WHERE account_id = :account_id AND guid = :guid"
                cursor.execute(sql, {"account_id": accounts[sourceAccountIndex]["id"], "guid": guid})
    elif handleExisting in ["r", "replace"]:
        # Remove existing viewstate items
        for entry in targetViewstate:
            sql = "DELETE FROM metadata_item_settings WHERE id = :id"
            cursor.execute(sql, {"id": entry["id"]})

if mode in ["c", "copy"]:
    print(f"Copying viewstate ({len(sourceViewstate)} items) "
          f"from {accounts[sourceAccountIndex]['name']} to {accounts[targetAccountIndex]['name']}")

    for entry in sourceViewstate:
        sql = "INSERT INTO metadata_item_settings (account_id, guid, rating, view_offset, view_count, last_viewed_at, " \
              "created_at, updated_at, skip_count, last_skipped_at, changed_at, extra_data, last_rated_at) VALUES (?, " \
              "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        cursor.execute(sql, (
            accounts[targetAccountIndex]["id"],
            entry["guid"],
            entry["rating"],
            entry["view_offset"],
            entry["view_count"],
            entry["last_viewed_at"],
            entry["created_at"],
            entry["updated_at"],
            entry["skip_count"],
            entry["last_skipped_at"],
            entry["changed_at"],
            entry["extra_data"],
            entry["last_rated_at"]
        ))

    connection.commit()
elif mode in ["m", "move"]:
    print(f"Moving viewstate ({len(sourceViewstate)} items) "
          f"from {accounts[sourceAccountIndex]['name']} to {accounts[targetAccountIndex]['name']}")

    sql = "UPDATE metadata_item_settings SET account_id = :target_account_id WHERE account_id = :source_account_id"
    cursor.execute(sql, {
        "target_account_id": accounts[targetAccountIndex]["id"],
        "source_account_id": accounts[sourceAccountIndex]["id"]
    })

    connection.commit()

cursor.close()
connection.close()
