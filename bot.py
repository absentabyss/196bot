#-------#
# Init. #
#-------#

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
import custom
import logging
import pickle
import subprocess as subproc    # Hehehe.
import utils

###
# Permissions. Only certain users can run certain commands. The users are
# registered with their user_ids on the file "allowed_users."
###

ALLOWED_USERS = []
with open("allowed_users", 'r') as f:
    for l in f:
        ALLOWED_USERS.append(int(l.strip('\n')))

# A custom class is used to raise exceptions on unauthorized usage.
class UnauthorizedExecution(Exception):
    pass

###
# ROM. Stores "registries" for users in which registers store strings.
###

# rom = {user_id: [active_label, {label: string}]}
try:
    with open("rom.pickle", "rb") as f:
        rom = pickle.load(f)
except:
    rom = {}

###
# Telegram bot initialization.
###

with open("token", 'r') as f:
    TOKEN = f.readline().strip('\n')

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO)

#----------------------#
#  Handler functions.  #
#----------------------#

###
# Generic bot functions.
###

# Called with: /ping
def ping(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Pong.",
        disable_notification=True)

# Called with: /help
def help(update, context):
    help_message = ""
    with open("help_message", 'r') as f:
        for l in f:
            help_message += l
    context.bot.send_message(chat_id=update.effective_chat.id,
            text=help_message,
        disable_notification=True)

# Assumes that this file is being run with a wrapper that restarts it.
def restart_bot(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    utils.stop_process()

# The bot will send all errors except for UnauthorizedExecution.
def callback(update, context):
    if type(context.error) != UnauthorizedExecution:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text=repr(context.error),
            disable_notification=True)

###
# Register functions. Users load registers with information and then write the
# content of those registers into files.
###

# Only one register per user can be in use at a time. When a register is in use
# by a user, the bot will ignore most commands until that register is
# "released."

# Called with: /in <label>
def register_request(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) != 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /in <register_label>",
            disable_notification=True)
        return
    label = context.args[0]

    rom = utils.create_registry_if_inexistent(rom, update)

    # Marks the label as active.
    rom[update.effective_user.id][0] = label

# It inserts any message from a user into the user's active register.
def register_insert(update, context):
    global rom
    if not utils.writing_to_rom(rom, update):
        return

    label = rom[update.effective_user.id][0]

    # Sets up register to be written on.
    if label not in rom[update.effective_user.id][1].keys():
        rom[update.effective_user.id][1][label] = ""

    # Writes message to register.
    if rom[update.effective_user.id][1][label]:
        rom[update.effective_user.id][1][label] += '\n'
    rom[update.effective_user.id][1][label] += update.message.text

# Called with: /ni
def register_release(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    # Checks if there's a label to release.
    if not utils.writing_to_rom(rom, update):
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="No register to release.",
            disable_notification=True)
        return
    label = rom[update.effective_user.id][0]

    # Sets the active label as None.
    rom[update.effective_user.id][0] = None

    # Saves the ROM for persistance.
    utils.save_rom(rom)

# Some functions to read registers.

# Called with: /regs
def registry_show(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    rom = utils.create_registry_if_inexistent(rom, update)

    # Compose message.
    content = "Registers: "
    for k in rom[update.effective_user.id][1].keys():
        content += k + ", "
    content = content.strip(", ")
    content += '.'

    context.bot.send_message(chat_id=update.effective_chat.id,
        text=content,
        disable_notification=True)

# Called with: /print <label>
def register_print(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) != 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /print <register_label>",
            disable_notification=True)
        return
    label = context.args[0]

    if utils.register_is_empty(rom, label, update, context):
        return

    content = rom[update.effective_user.id][1][label]
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=content,
        disable_notification=True)

# Some functions to clear registers.

# Called with: /clear <label>
def register_clear(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) != 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /clear <register_label>",
            disable_notification=True)
        return
    label = context.args[0]

    if utils.register_is_empty(rom, label, update, context):
        return

    # Clears register.
    del rom[update.effective_user.id][1][label]

    utils.save_rom(rom)

# Called with: /clear_all
def rom_clear(update, context):
    global rom
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Clear user's rom.
    if update.effective_user.id in rom.keys():
        del rom[update.effective_user.id]

    utils.save_rom(rom)

###
# Shell functions. The bot runs coreutils to deal with the file system (primarily with
# "sed"). These provide capabilities for writing to, reading from, deleting, and
# creating files.
###

# Functions to read from the file system.

# Called with: /ls <dir>
def explore_directory(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Ls execution.
    command = ["ls"]
    command += context.args
    try:
        out = subproc.check_output(command,
            encoding="UTF-8").split('\n')
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return

    # Response composition.
    message = ""
    for i in range(len(out)):
        message += out[i] + ", "

    context.bot.send_message(chat_id=update.effective_chat.id,
        text=message,
        disable_notification=True)

# Called with: /read <file> <line_start> <line_end>
def read_lines_from_file(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) not in [1, 2, 3]:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /read <file> <line_start> <line_end>",
            disable_notification=True)
        return
    for i in range(1, len(context.args)):
        try:
            context.args[i] = int(context.args[i])
        except:
            return
    if len(context.args) == 1:
        context.args.append(1)
    if len(context.args) == 2:
        context.args.append(context.args[1] + 5)

    # Sed execution. Sed gets the requested lines from the file.
    filename = context.args[0]
    line_start = context.args[1]
    line_end = context.args[2]
    try:
        out = subproc.check_output(["sed", "-n",
            "{},{}p".format(line_start, line_end), filename],
            encoding="UTF-8").split('\n')
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return

    # Stdout to message conversion. Adds line number to output.
    message = ""
    for i in range(len(out)):
        message += str(i + line_start) + ' ' + out[i] + '\n'

    context.bot.send_message(chat_id=update.effective_chat.id,
        text=message,
        disable_notification=True)

# Functions to edit files from the file system.

# Called with: /new <label> <file>
def dump_to_new_file(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) != 2:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /new <label> <file>",
            disable_notification=True)
        return

    label = context.args[0]
    filename = context.args[1]

    if utils.register_is_empty(rom, label, update, context):
        return

    # Dump to file.
    content = rom[update.effective_user.id][1][label]

    try:
        with open(filename, 'x') as f:
            f.write(content)
        utils.ensure_trailing_newline(filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return
    
    utils.git_commit("Wrote register {} to file {}.".format(label, filename))
    return

# Called with: /inject <label> <file> <line>
def inject_into_existing_file(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) not in [2, 3]:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /inject <label> <file> <line>",
            disable_notification=True)
        return

    if len(context.args) == 2:
        context.args.append(1)

    try:
        context.args[2] = int(context.args[2])
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /inject <label> <file> <line>",
            disable_notification=True)
        return

    label = context.args[0]
    filename = context.args[1]
    line = context.args[2]

    if utils.register_is_empty(rom, label, update, context):
        return

    # Inserts to file.

    # First determines if it should append to file or inject.
    if line > utils.count_lines_in_file(filename):
        try:
            utils.ensure_trailing_newline(filename)
            with open(filename, "a") as f:
                content = rom[update.effective_user.id][1][label]
                f.write(content)
            utils.ensure_trailing_newline(filename)
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                text="-1",
                disable_notification=True)
            return

        utils.git_commit("Appended contents of register {} to file {}.".format(label, filename))
        return

    try:
        # Ensures the register can be read by Sed.
        content = repr(rom[update.effective_user.id][1][label])[1:-1]
        command = ["sed", "-i", "{} i {}".format(line, content), filename]
        utils.ensure_trailing_newline(filename)
        subproc.run(command, check=True)
        utils.ensure_trailing_newline(filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return

    utils.git_commit(
            "Injected contents of register {} into line {} of file {}.".format(label, line, filename)
    )
    return

# Called with: /overwrite <label> <file> <line_start> <line_end>
def overwrite_lines_in_file(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) not in [3, 4]:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /overwrite <label> <file> <line_start> <line_end>",
            disable_notification=True)
        return
    if len(context.args) == 3:
        context.args.append(context.args[-1])
    for i in range(2, len(context.args)):
        try:
            context.args[i] = int(context.args[i])
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                text="Correct format: /overwrite <label> <file> <line_start> <line_end>",
                disable_notification=True)
            return

    label = context.args[0]
    filename = context.args[1]
    line_start = context.args[2]
    line_end = context.args[3]

    if utils.register_is_empty(rom, label, update, context):
        return

    # Line trimming.
    try:
        command = ["sed", "-i", "{},{}d".format(line_start, line_end), filename]
        utils.ensure_trailing_newline(filename)
        subproc.run(command, check=True)
        utils.ensure_trailing_newline(filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return

    # Inserts to file.

    # First determines if it should append to file or inject.
    if line_start > utils.count_lines_in_file(filename):
        try:
            utils.ensure_trailing_newline(filename)
            with open(filename, "a") as f:
                content = rom[update.effective_user.id][1][label]
                f.write(content)
            utils.ensure_trailing_newline(filename)
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                text="-1",
                disable_notification=True)
            return

        utils.git_commit(
            "Overwrote from line {} to line{} of file {} with contents of register {}.".format(line_start, line_end, filename, label)
        )
        return

    try:
        # Ensures the register can be read by Sed.
        content = repr(rom[update.effective_user.id][1][label])[1:-1]
        command = ["sed", "-i", "{} i {}".format(line_start, content), filename]
        utils.ensure_trailing_newline(filename)
        subproc.run(command, check=True)
        utils.ensure_trailing_newline(filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return

    utils.git_commit(
        "Overwrote from line {} to line{} of file {} with contents of register {}.".format(line_start, line_end, filename, label)
    )
    return

# Called with: /trim <file> <line_start> <line_end>
def trim_lines_from_file(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    # Input curation.
    if len(context.args) not in [2, 3]:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="Correct format: /trim <file> <line_start> <line_end>",
            disable_notification=True)
        return
    if len(context.args) == 2:
        context.args.append(context.args[1])
    for i in range(1, len(context.args)):
        try:
            context.args[i] = int(context.args[i])
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                text="Correct format: /trim <file> <line> <line>",
                disable_notification=True)
            return
    
    filename = context.args[0]
    line_start = context.args[1]
    line_end = context.args[2]

    # Line trimming.
    try:
        command = ["sed", "-i", "{},{}d".format(line_start, line_end), filename]
        utils.ensure_trailing_newline(filename)
        subproc.run(command, check=True)
        utils.ensure_trailing_newline(filename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
            text="-1",
            disable_notification=True)
        return
    utils.git_commit(
        "Deleted from line {} to line {} of file {}.".format(line_start, line_end, filename)
    )
    return

###
# Custom handler. Imports extra user-defined functionalities from Custom.py.
###

def custom_functions(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        raise UnauthorizedExecution

    if utils.must_release_rom(rom, update, context):
        return

    custom.core(update, context)
    return

#-----------#
# Handlers. #
#-----------#

restart_handler = CommandHandler("restart", restart_bot)
dispatcher.add_handler(restart_handler)

ping_handler = CommandHandler("ping", ping)
dispatcher.add_handler(ping_handler)

help_handler = CommandHandler("help", help)
dispatcher.add_handler(help_handler)

in_handler = CommandHandler("in", register_request)
dispatcher.add_handler(in_handler)

ni_handler = CommandHandler("ni", register_release)
dispatcher.add_handler(ni_handler)

registry_show_handler = CommandHandler("regs", registry_show)
dispatcher.add_handler(registry_show_handler)

print_handler = CommandHandler("print", register_print)
dispatcher.add_handler(print_handler)

clear_handler = CommandHandler("clear", register_clear)
dispatcher.add_handler(clear_handler)

clear_all_handler = CommandHandler("clear_all", rom_clear)
dispatcher.add_handler(clear_all_handler)

ls_handler = CommandHandler("ls", explore_directory)
dispatcher.add_handler(ls_handler)

read_handler = CommandHandler("read", read_lines_from_file)
dispatcher.add_handler(read_handler)

trim_handler = CommandHandler("trim", trim_lines_from_file)
dispatcher.add_handler(trim_handler)

dump_handler = CommandHandler("new", dump_to_new_file)
dispatcher.add_handler(dump_handler)

overwrite_handler = CommandHandler("overwrite", overwrite_lines_in_file)
dispatcher.add_handler(overwrite_handler)

insert_handler = CommandHandler("inject", inject_into_existing_file)
dispatcher.add_handler(insert_handler)

register_insert_handler = MessageHandler(Filters.text, register_insert)
dispatcher.add_handler(register_insert_handler)

dispatcher.add_error_handler(callback)

custom_handler = MessageHandler(Filters.text, custom_functions)
dispatcher.add_handler(custom_handler, 1)


###
# Polling.
###

updater.start_polling()
