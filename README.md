# 196bot
Telegram bot designed to allow the user to _easily_ edit the bot's code from the Telegram chat.

**Warning**: In its current version it allows the user to edit any text file, even outside the bot's source code. Use carefully.

### How to run
```
./init.sh
```

### Info
The bot should have 3 components:
- A simple text editor that takes strings and inserts them somewhere. This text
  editor can also read strings from somewhere.
- The running part of the bot.
- A wrapper that restarts the bot, and holds backups in case the bot fails.

The bot must be private, otherwise other people could corrupt it or worse, the
filesystem (though the bot could technically be run as a separate user).

### Functions
/ping: Replies with "Pong."

/help: Displays help message.

/in [register_label]: Activates a register for the user. The following messages
from the user will be stored inside the register until the register is released
with /ni.

/ni: Releases the active register for the user.

/regs: Lists all non-empty registers of the user.

/print [register_label]: Shows the content of a register.

/clear [register_label]: Clears register.

/clear_all: Clears registry containing all registers for the user.

/ls [directory]: Checks directories.

/read [file] [line_start] [line_end]: Reads from line_start to line_end from file.

/new [register_label] [file]: Writes the contents of a register into a new file.

/inject [register_label] [file] [line]: Writes the contents of a register at a
line in file.

/overwrite [label] [file] [line_start] [line_end]: Overwrites from line_start to
line_end of file with the contents of a register.

/trim [file] [line_start] [line_end]: Deletes from line_start to line_end in file.

/revert: Reverts files to a previous version.

/restart: Restarts the bot.
