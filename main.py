# Python için örnek kod (main.py)
import os
import json
import requests

# WhatsApp Business API ayarları
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages"
# Güvenlik için bu token'ı ortam değişkenlerinde saklayın.
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
HEDEF_NUMARA = "449999999999" # Mesajları yönlendirmek istediğiniz numara

def whatsapp_webhook(request):
    # WhatsApp'ın doğrulama isteğini işleme (ilk kurulum için gereklidir)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        # 'YOUR_VERIFY_TOKEN' yerine kendi belirlediğiniz token'ı koyun
        if mode == 'subscribe' and token == 'YOUR_VERIFY_TOKEN':
            print('Webhook doğrulandı!')
            return challenge, 200
        return 'Doğrulama başarısız.', 403

    # Gelen mesaj verisini işleme
    if request.method == 'POST':
        try:
            data = request.get_json()
            entry = data['entry'][0]
            if 'changes' in entry and entry['changes'][0]['value']['messages']:
                messages = entry['changes'][0]['value']['messages']
                incoming_message = messages[0]

                gonderen_numara = incoming_message['from']
                mesaj_icerigi = incoming_message['text']['body']

                print(f"Gelen mesaj: {mesaj_icerigi} - Gönderen: {gonderen_numara}")

                # Yönlendirme mesajını oluşturma
                yonlendirme_mesaji = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": HEDEF_NUMARA,
                    "type": "text",
                    "text": {
                        "body": f"Gelen Mesaj ({gonderen_numara}): {mesaj_icerigi}"
                    }
                }

                # WhatsApp API'ye mesajı gönderme
                headers = {
                    'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                response = requests.post(WHATSAPP_API_URL, json=yonlendirme_mesaji, headers=headers)
                
                print('Mesaj başarıyla yönlendirildi:', response.json())
                return 'OK', 200
            else:
                return 'OK', 200
        except Exception as e:
            print(f'Hata oluştu: {e}')
            return 'Hata', 500
