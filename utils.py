import os
import pickle
import subprocess as subproc
from time import sleep

# Update and Context objects are provided by the python-telegram-bot updater.

# It's kind of ugly how I call this function before and after each write. But
# it's the simpliest way I could think of for ensuring proper formatting.
def ensure_trailing_newline(filename):
    subproc.run(["sed", "-i", "-e", "$ a \\", filename], check=True)

def count_lines_in_file(filename):
    try:
        wc = subproc.check_output(["wc", "-l", filename], encoding="UTF-8")
        lines = wc.split(' ')[0]
        lines = int(lines)
        return lines
    except:
        return -1

def save_rom(rom):
    with open("rom.pickle", "wb") as f:
        pickle.dump(rom, f, pickle.HIGHEST_PROTOCOL)

# Some commands require the no register to be active.
def must_release_rom(rom, update, context):
    if update.effective_user.id in rom.keys() and rom[update.effective_user.id][0]:
        label = rom[update.effective_user.id][0]
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Release register {}.".format(label),
            disable_notification=True)
        return True
    return False

def writing_to_rom(rom, update):
    if (
            update.effective_user.id in rom.keys()
            and rom[update.effective_user.id][0]
    ):
        return True
    return False

def register_is_empty(rom, label, update, context):
    if (
            update.effective_user.id not in rom.keys()
            or label not in rom[update.effective_user.id][1].keys()
    ):
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Register {} is empty.".format(label),
            disable_notification=True)
        return True
    return False

def create_registry_if_inexistent(rom, update):
    if update.effective_user.id not in rom.keys():
        rom[update.effective_user.id] = [None, {}]
    return rom

def git_commit(message):
    command = ["git", "add", "-A"]
    subproc.run(command, check=True)
    command = ["git", "commit", "-m", message]
    subproc.run(command, check=True)

# This is ugly, but it prevents the process from perpetually shutting down.
def stop_process():
    sleep(1)
    os.kill(os.getpid(), 15)
