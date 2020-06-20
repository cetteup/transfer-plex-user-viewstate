import argparse
import sqlite3

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


parser = argparse.ArgumentParser('Transfer Plex user viewstate between users')
parser.add_argument("-p", "--db-path", help="Path to com.plexapp.plugins.library.db file")
args = parser.parse_args()

connection = sqlite3.connect(args.db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

# Get users
cursor.execute("SELECT id, name, created_at FROM accounts WHERE id > 0")
accounts = cursor.fetchall()
accountIds = [str(a["id"]) for a in accounts]

# Print users
print(tabulate([{"index": i, "name": accounts[i]["name"]} for i in range(0, len(accounts))], headers="keys"))

# Ask user to select source user
sourceAccountIndex = int(get_valid_input(
    "Please enter the _source_ account index",
    str_range(len(accounts)),
    "No account with that ID, please enter a valid account index"
))

# Ask user to select target user
targetUserIndex = int(get_valid_input(
    "Please enter the _target_ account index",
    str_range(len(accounts)),
    "No account with that ID, please enter a valid account index"
))

# Ask user to select copying/moving view state
mode = get_valid_input(
    "Do want to copy or move the viewstate? (copy/move)",
    ["c", "copy", "m", "move"],
    "Please select either (c)opy or (m)ove"
)

# Get source account viewstate
sql = "SELECT * FROM metadata_item_settings WHERE account_id = :account_id"
cursor.execute(sql, {"account_id": accounts[sourceAccountIndex]['id']})
sourceViewstate = cursor.fetchall()

if mode in ["c", "copy"]:
    print(f"Copying viewstate ({len(sourceViewstate)} items) "
          f"from {accounts[sourceAccountIndex]['name']} to {accounts[targetUserIndex]['name']}")

    for entry in sourceViewstate:
        sql = "INSERT INTO metadata_item_settings (account_id, guid, rating, view_offset, view_count, last_viewed_at, " \
              "created_at, updated_at, skip_count, last_skipped_at, changed_at, extra_data, last_rated_at) VALUES (?, " \
              "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        cursor.execute(sql, (
            accounts[targetUserIndex]["id"],
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
          f"from {accounts[sourceAccountIndex]['name']} to {accounts[targetUserIndex]['name']}")

    sql = "UPDATE metadata_item_settings SET account_id = :target_account_id WHERE account_id = :source_account_id"
    cursor.execute(sql, {
        "target_account_id": accounts[targetUserIndex]["id"],
        "source_account_id": accounts[sourceAccountIndex]["id"]
    })

    connection.commit()

cursor.close()
connection.close()
