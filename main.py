import os
import json
import requests
from flask import Flask, request, Response

# Ortam değişkenlerini alıyoruz. Google Cloud'da ayarladığınız isimlerle aynı olmalı.
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
RECIPIENT_NUMBER = os.environ.get('RECIPIENT_NUMBER')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')

# Flask uygulamasını başlatıyoruz. Cloud Functions bunu arka planda kullanır.
app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Bu fonksiyon hem WhatsApp webhook doğrulamasını yapar (GET)
    hem de gelen mesajları alıp yönlendirir (POST).
    """
    if request.method == 'GET':
        # Bu blok, Meta'nın webhook URL'nizi doğrulaması içindir.
        # Meta for Developers paneline webhook'u eklediğinizde çalışır.
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        else:
            return 'Error, wrong validation token', 403

    if request.method == 'POST':
        # Bu blok, WhatsApp'tan gelen mesajları işler.
        try:
            data = request.get_json()
            
            # Gelen verinin bir mesaj içerip içermediğini kontrol et
            if 'entry' in data and data['entry'][0]['changes'][0]['value'].get('messages'):
                message = data['entry'][0]['changes'][0]['value']['messages'][0]
                
                # Sadece text mesajlarını yönlendir
                if message['type'] == 'text':
                    sender_number = message['from']
                    message_body = message['text']['body']
                    
                    # Yönlendirilecek mesajın formatını oluştur
                    forwarded_message = f"Yeni Mesaj Var:\n\n*Gönderen:* {sender_number}\n*Mesaj:* {message_body}"
                    
                    # Mesajı yönlendirme fonksiyonunu çağır
                    send_whatsapp_message(RECIPIENT_NUMBER, forwarded_message)
            
            return 'OK', 200

        except Exception as e:
            print(f"Hata olustu: {e}")
            # Bir hata olsa bile WhatsApp'a başarılı yanıt dönmek önemlidir,
            # aksi takdirde size bildirim göndermeyi durdurabilir.
            return 'Error processing request', 200

def send_whatsapp_message(to_number, message_text):
    """
    Belirtilen numaraya WhatsApp mesajı gönderir.
    """
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # HTTP hata kodları için exception fırlatır
        print(f"Mesaj basariyla gonderildi. Status: {response.status_code}, Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Mesaj gonderilirken hata: {e}")

# Cloud Functions'ın bu uygulamayı çalıştırması için
# Giriş noktası (Entry Point) olarak bu fonksiyonun adını vermelisiniz.
# Bu örnekte "Giriş Noktası" = whatsapp_webhook
def main(request):
    """
    Google Cloud Functions için ana giriş noktası.
    İsteği Flask uygulamasına yönlendirir.
    """
    # Cloud Functions ortamı için bir context oluştur
    with app.request_context(request.environ):
        # İsteği Flask'in işlemesine izin ver
        return app.full_dispatch_request()
