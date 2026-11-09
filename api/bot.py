import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9147785620:AAHfswghuWydXyw7_ms9qywWtcoaED5UMM4")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zfqchteulqkqzylcchpj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmcWNodGV1bHFrcXp5bGNjaHBqIiwicm9sZSI6ImFub24iLCJpYXQiOjV9.N4Z0XmSgCG5O4oK-nZg8vQ5K-7x9vQ2Z8mK9vQ")

def get_supabase_data():
    """Supabase REST API ile anlık veri çekme"""
    url = f"{SUPABASE_URL}/rest/v1/trades?select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Supabase hata: {e}")
    return []

def send_telegram_message(chat_id, text):
    """Telegram'a yanıt gönderme fonksiyonu"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "").strip()
                
                if text == "/start":
                    reply = (
                        "🤖 **SMC & Price Action İstek Tabanlı Bot**\n\n"
                        "Komut gönderdiğiniz an Supabase'den veriler çekilir:\n"
                        "🔍 `/tara` - Güncel sinyalleri listeler.\n"
                        "📊 `/durum` - Açık pozisyonları gösterir.\n"
                        "📈 /istatistik - Genel kâr/zarar özetini sunar."
                    )
                    send_telegram_message(chat_id, reply)
                    
                elif text == "/tara":
                    trades = get_supabase_data()
                    if not trades:
                        send_telegram_message(chat_id, "📂 Supabase veritabanında şu an kayıtlı sinyal yok.")
                    else:
                        resp = "🚀 **Supabase Güncel Sinyaller:**\n\n"
                        for t in trades[-4:]:
                            resp += f"✅ **{t.get('symbol')}** ({t.get('type')})\nGiriş: `${t.get('entry_price')}` | SL: `${t.get('sl')}`\n\n"
                        send_telegram_message(chat_id, resp)
                        
                elif text == "/durum":
                    trades = get_supabase_data()
                    open_trades = [t for t in trades if str(t.get("status", "")).upper() == "OPEN"]
                    if not open_trades:
                        send_telegram_message(chat_id, "📂 Şu an açık pozisyon bulunmuyor.")
                    else:
                        resp = "📊 **Açık Pozisyonlar:**\n\n"
                        for t in open_trades:
                            resp += f"• **{t.get('symbol')}** | Giriş: `${t.get('entry_price')}`\n"
                        send_telegram_message(chat_id, resp)
                        
                else:
                    send_telegram_message(chat_id, "❓ Bilinmeyen komut. /tara veya /durum yazabilirsiniz.")
                    
        except Exception as e:
            print(f"Hata: {e}")
            
        self.send_response(200)
        self.end_headers()
        return

