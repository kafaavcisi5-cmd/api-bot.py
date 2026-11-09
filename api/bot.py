import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9147785620:AAHfswghuWydXyw7_ms9qywWtcoaED5UMM4")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zfqchteulqkqzylcchpj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmcWNodGV1bHFrcXp5bGNjaHBqIiwicm9sZSI6ImFub24iLCJpYXQiOjV9.N4Z0XmSgCG5O4oK-nZg8vQ5K-7x9vQ2Z8mK9vQ")

def get_supabase_data():
    """Supabase REST API ile güvenli veri çekme"""
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
    """Telegram'a yanıt gönderme"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
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
                            "📈 `/istatistik` - Genel özet sunar.\n"
                            "📜 `/gecmis` - Tamamlanan işlemleri listeler."
                        )
                        send_telegram_message(chat_id, reply)
                        
                    elif text == "/tara":
                        trades = get_supabase_data()
                        if not trades:
                            send_telegram_message(chat_id, "📂 Supabase veritabanında şu an kayıtlı sinyal yok.")
                        else:
                            resp = "🚀 **Supabase Güncel Sinyaller:**\n\n"
                            for t in trades[-4:]:
                                symbol = t.get('symbol', 'Bilinmiyor')
                                t_type = t.get('type', '')
                                entry = t.get('entry_price', '0')
                                sl = t.get('sl', '0')
                                resp += f"✅ **{symbol}** ({t_type})\nGiriş: `${entry}` | SL: `${sl}`\n\n"
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

                    elif text == "/istatistik":
                        trades = get_supabase_data()
                        total = len(trades)
                        resp = f"📈 **Genel İstatistikler:**\n\n• Toplam Kayıtlı İşlem: {total}\n• Durum: Aktif ve Senkronize"
                        send_telegram_message(chat_id, resp)

                    elif text == "/gecmis":
                        trades = get_supabase_data()
                        closed_trades = [t for t in trades if str(t.get("status", "")).upper() != "OPEN"]
                        if not closed_trades:
                            send_telegram_message(chat_id, "📜 Tamamlanmış geçmiş işlem bulunmuyor.")
                        else:
                            resp = "📜 **Geçmiş İşlemler:**\n\n"
                            for t in closed_trades[-3:]:
                                resp += f"• **{t.get('symbol')}** - Sonuç: {t.get('status', 'Kapandı')}\n"
                            send_telegram_message(chat_id, resp)
                            
                    else:
                        send_telegram_message(chat_id, "❓ Bilinmeyen komut. /start ile komutları görebilirsiniz.")
        except Exception as e:
            print(f"Genel İşleme Hatası: {e}")
            
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "Bot is running!"}')
        return
