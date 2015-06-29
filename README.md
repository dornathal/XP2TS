# XP2TS
Connects IvAp with Teamspeak2 on Linux systems

## Overview
As X-IvAp does not change the TS Channels automaticly this plugin manages TS2 Server and channel switches completely in the background.

## Installation

- a. Install the [PythonInterface Plugin]
- b. Put the PI_XP2TS.py Script into the ./Resources/plugins/PythonScripts folder
- c. Now simply modify the PI_XP2TS.py file:
-  1. PI_XP2TS    : __ResourcePath = "/absolute/path/to/Resources/plugins/X-IvAp Resources/"
-  2. X-IvAp.conf : Füge folgendes hinzu:

    [TEAMSPEAK]<br />
    tscontrol = "/absolute/path/to/the/TeamSpeak/Folder"<br />
    server = eu4 <br />

eu4 can be replaced by any available TS Server Prefix. It is beeing overriden after each login. That way it is safe if a server closes in the future 

## Features
- No longer has to be started seperately
- Callsign and login informations will be used from the X-IvAp.conf File.
- After relogging with a different Callsign the change will be synchronised by the next channelswitch.
- easier installation (only one file)

## ToDo
- I'm not quite sure weather the swap to Channels with 8.33kHz will work always. As X-Plane does only provide 2 decimals. 120.175 e.g. is transmitted as 120.17. In that case I match every frequence from 120.16 to 120.18. The closest open ATC Station that matches the frequency will be connected in TS2.

## Credits
The original Contributor of the Source is Enrico Gallesio who did an incredible work. 
