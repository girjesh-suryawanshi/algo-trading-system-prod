import requests, os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    """
    Sends a message to the configured Telegram chat.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"Alert (No Telegram Config): {message}")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚀 *Algo Alert*\n\n{message}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def alert_entry(symbol, strike, price):
    send_alert(f"✅ *ENTRY TRIGGERED*\nSymbol: {symbol}\nStrike: {strike}\nPrice: ₹{price}")

def alert_exit(symbol, strike, price, pnl):
    icon = "💰" if pnl > 0 else "🛑"
    send_alert(f"{icon} *EXIT TRIGGERED*\nSymbol: {symbol}\nStrike: {strike}\nPrice: ₹{price}\nPnL: ₹{pnl}")
