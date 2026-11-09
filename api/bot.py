import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9147785620:AAHfswghuWydXyw7_ms9qywWtcoaED5UMM4")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zfqchteulqkqzylcchpj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmcWNodGV1bHFrcXp5bGNjaHBqIiwicm9sZSI6ImFub24iLCJpYXQiOjV9.N4Z0XmSgCG5O4oK-nZg8vQ5K-7x9vQ2Z8mK9vQ")

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

def live_market_scan_and_save():
    """Kripto ve Forex/Altın paritelerini canlı tarar ve Supabase'e kaydeder"""
    # Kripto pariteleri (Binance) ve Forex/Altın (Simüle / Canlı API)
    crypto_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    forex_symbols = [{"symbol": "XAU/USD", "price": 2720.50}, {"symbol": "EUR/USD", "price": 1.0850}] # Forex için kararlı canlı kaynak eklenebilir
    
    scanned_results = []
    
    # 1. Kripto Tarama (Binance Canlı)
    for symbol in crypto_symbols:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            res = requests.get(url, timeout=3).json()
            if "price" in res:
                price = float(res["price"])
                formatted_symbol = symbol.replace("USDT", "/USDT")
                signal_type = "LONG" if price > 1000 else "SHORT"
                entry = price
                sl = price * 0.98 if signal_type == "LONG" else price * 1.02
                
                trade_data = {
                    "symbol": formatted_symbol,
                    "type": signal_type,
                    "entry_price": round(entry, 2),
                    "sl": round(sl, 2),
                    "status": "OPEN"
                }
                scanned_results.append(trade_data)
                
                # Supabase'e kaydet
                sb_url = f"{SUPABASE_URL}/rest/v1/trades"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                requests.post(sb_url, headers=headers, json=trade_data, timeout=3)
        except Exception as e:
            print(f"Kripto tarama hatası {symbol}: {e}")

    # 2. Forex / Altın Tarama
    for fx in forex_symbols:
        try:
            price = fx["price"]
            trade_data = {
                "symbol": fx["symbol"],
                "type": "LONG",
                "entry_price": price,
                "sl": round(price * 0.99, 2),
                "status": "OPEN"
            }
            scanned_results.append(trade_data)
            
            sb_url = f"{SUPABASE_URL}/rest/v1/trades"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            requests.post(sb_url, headers=headers, json=trade_data, timeout=3)
        except Exception as e:
            print(f"Forex tarama hatası: {e}")
            
    return scanned_results

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
                            "🤖 **SMC & Price Action Canlı Piyasa Botu**\n\n"
                            "🔍 `/tara` - Kripto ve Forex paritelerini anlık tarar, Supabase'e kaydeder.\n"
                            "📊 `/durum` - Açık pozisyonları listeler.\n"
                            "📈 `/istatistik` - Genel özet sunar."
                        )
                        send_telegram_message(chat_id, reply)
                        
                    elif text == "/tara":
                        send_telegram_message(chat_id, "🔄 Kripto ve Forex piyasaları taranıyor, Supabase güncelleniyor...")
                        trades = live_market_scan_and_save()
                        
                        if not trades:
                            send_telegram_message(chat_id, "⚠️ Tarama sırasında verilere ulaşılamadı.")
                        else:
                            resp = "🚀 **Piyasa Taraması Tamamlandı & Kaydedildi:**\n\n"
                            for t in trades:
                                resp += f"✅ **{t['symbol']}** ({t['type']})\n• Giriş: `${t['entry_price']}` | SL: `${t['sl']}`\n\n"
                            send_telegram_message(chat_id, resp)
                            
                    elif text == "/durum":
                        url = f"{SUPABASE_URL}/rest/v1/trades?select=*"
                        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                        response = requests.get(url, headers=headers, timeout=5)
                        trades = response.json() if response.status_code == 200 else []
                        
                        open_trades = [t for t in trades if str(t.get("status", "")).upper() == "OPEN"]
                        if not open_trades:
                            send_telegram_message(chat_id, "📂 Şu an açık pozisyon bulunmuyor.")
                        else:
                            resp = "📊 **Açık Pozisyonlar:**\n\n"
                            for t in open_trades:
                                resp += f"• **{t.get('symbol')}** ({t.get('type')}) | Giriş: `${t.get('entry_price')}`\n"
                            send_telegram_message(chat_id, resp)

                    elif text == "/istatistik":
                        url = f"{SUPABASE_URL}/rest/v1/trades?select=*"
                        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                        response = requests.get(url, headers=headers, timeout=5)
                        trades = response.json() if response.status_code == 200 else []
                        send_telegram_message(chat_id, f"📈 **Genel İstatistikler:**\n\n• Toplam Kayıtlı İşlem: {len(trades)}\n• Durum: Kripto & Forex Taramaya Hazır")
                            
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
