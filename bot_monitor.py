import subprocess
import time
import requests
import threading
import os

# Telegram sozlamalari
MONITOR_BOT_TOKEN = "8502137302:AAGwkqg548VhXVEw74RB5K-duKkQTcMcDVs"
MONITOR_CHAT_ID = "7917659197"

BOT_NAME = "xovosbot"
BOT_PATH = "/home/hasan/xovos_2_maktab_bot/bot.py"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{MONITOR_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": MONITOR_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Xabar yuborilmadi: {e}")

def monitor_bot():
    while True:
        try:
            result = subprocess.run(["systemctl", "is-active", BOT_NAME], capture_output=True, text=True)
            status = result.stdout.strip()
            if status != "active":
                send_telegram(f"⚠️ {BOT_NAME} ishlamayapti! Qayta ishga tushirilyapti...")
                subprocess.run(["sudo", "systemctl", "restart", BOT_NAME])
        except Exception as e:
            send_telegram(f"❌ Monitoring xato: {e}")
        time.sleep(300)  # har 5 daqiqada tekshiradi

def run_bot():
    # Botni ishga tushirish
    os.system(f"/home/hasan/xovos_2_maktab_bot/venv/bin/python {BOT_PATH}")

if __name__ == "__main__":
    threading.Thread(target=monitor_bot, daemon=True).start()
    run_bot()
