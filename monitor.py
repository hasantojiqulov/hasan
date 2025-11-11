import subprocess
import time
import requests

# Telegram sozlamalari
BOT_TOKEN = "8502137302:AAGwkqg548VhXVEw74RB5K-duKkQTcMcDVs"
CHAT_ID = "7917659197"

BOT_NAME = "xovosbot"  # systemd service nomi

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"Xabar yuborilmadi: {e}")

def check_bot():
    try:
        # systemctl holatini tekshiradi
        result = subprocess.run(["systemctl", "is-active", BOT_NAME], capture_output=True, text=True)
        status = result.stdout.strip()
        if status != "active":
            send_telegram(f"⚠️ {BOT_NAME} ishlamayapti! Hozir qayta ishga tushirilyapti...")
            subprocess.run(["sudo", "systemctl", "restart", BOT_NAME])
        else:
            print(f"{BOT_NAME} ish holati: {status}")
    except Exception as e:
        send_telegram(f"❌ Botni tekshirishda xato: {e}")

if __name__ == "__main__":
    while True:
        check_bot()
        time.sleep(300)  # har 5 daqiqada tekshiradi
