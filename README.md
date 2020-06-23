# transfer-plex-user-viewstate
Transfer Plex viewstate information (watched/unwatched, view progress and ratings) between accounts on a Plex Media Server

## Features
- copying complete viewstate from one Plex account/user to another
- moving complete viewstate from one Plex account/user to another
- support for managed users, admin user and full Plex accounts
- interactive command line interface

## Command line arguments
Argument (short/long)|Description|Required
---------------------|-----------|--------
`-p`/`--db-path`|Path to com.plexapp.plugins.library.db file|Yes

## How to run
**Please note:** Make sure to stop Plex Media Server before using the transfer script. Running the script while Plex is running may result in database corruption. I strongly advise creating a backup of the database file before running the script.
### On Windows
1. Download and extract the [latest release](https://github.com/cetteup/transfer-plex-user-viewstate/releases/latest) for Windows
2. Stop Plex Media Server by right-clicking onto the system tray icon and then clicking "Exit"
3. Open a Powershell window
4. Enter the path to the release's transfer-plex-user-viewstate.exe (can be done by simply dragging it onto the Powershell window)
5. Enter `-p` or `--db-path` followed by the path to the com.plexapp.plugins.library.db file, which is located in the Plex data directory (check the [Plex documentation](https://support.plex.tv/articles/202915258-where-is-the-plex-media-server-data-directory-located/) for details on how to find it)
6. Make sure your command looks something like this: `C:\Users\cetteup\Downloads\transfer-plex-user-viewstate-0.1-windows\transfer-plex-user-viewstate.exe -p  "C:\Users\cetteup\AppData\Local\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db"`
7. Hit enter to run the command
8. Follow the instruction to select source and target account as well as the transfer mode (move/copy)
9. Once the transfer is complete, start Plex Media Server back up

### On Linux
1. Download and extract the [latest release](https://github.com/cetteup/transfer-plex-user-viewstate/releases/latest) for Linux
2. Open a terminal window
3. Stop the Plex Media Server service using `sudo service plexmediaserver stop`, `sudo systemctl stop plexmediaserver` or your preferred command for stopping a service (omit `sudo` if you are logged in as root)
4. Navigate to the downloaded release, e.g. `cd ~/Downloads/transfer-plex-user-viewstate-0.1-linux/`
5. Make sure you have execute permission for the transfer-plex-user-viewstate binary by running `chmod +x transfer-plex-user-viewstate`
6. Enter `./transfer-plex-user-viewstate` followed by `-p` or `--db-path` and the path to the com.plexapp.plugins.library.db file, which is located in the Plex data directory (check the [Plex documentation](https://support.plex.tv/articles/202915258-where-is-the-plex-media-server-data-directory-located/) for details on how to find it)
7. Make sure your command looks something like this: `./transfer-plex-user-viewstate -p /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db`
8. Hit enter to run the command
9. Follow the instruction to select source and target account as well as the transfer mode (move/copy)
10. Once the transfer is complete, start the Plex Media Server service back up (`sudo service plexmediaserver start`, `sudo systemctl start plexmediaserver`)

### Using Python (on any OS)
If you have Python >=3.6 installed on your system, you can use the Python script directly. No need to download the binary. Make sure to install required depencies first  (`pip3 install -r requirements.txt`).

## Known limitations
- users/accounts only appear in database after connecting to the server and/or playing a media item from it at least once
- script currently does not check whether target user already has viewstate information for a library item (may result in two conflicting viewstates)
- Tautulli ([A Python based monitoring and tracking tool for Plex Media Server](https://tautulli.com)) will not pick up any of the transferred viewstate information