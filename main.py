import requests
import json
from flask import Flask, request

# --- BAŞLANGIÇ: BİLGİLERİNİZİ BURAYA GİRİN ---

# Meta for Developers -> WhatsApp -> Configuration -> Webhooks bölümünde belirlediğiniz parola.
# Bu, Google ile Meta'nın birbirini doğrulaması için kullanılır.
VERIFY_TOKEN = "LVSH-Gizli-Parola"  # Lütfen bunu kendinize özel, tahmin edilmesi zor bir şeyle değiştirin.

# Meta for Developers -> WhatsApp -> API Setup panelinden kopyaladığınız jeton.
# DİKKAT: Bu geçici bir jetondur ve 24 saatte bir süresi dolar. 
# Kalıcı bir jeton oluşturup buraya yapıştırmanız gerekir.
ACCESS_TOKEN = "EAALfbjDsgbgBPATsd31ZZhKoCEawRuZAK5mykTVoFIDKWIFWi0wSGZCzCXQ59EEOWIZ1JiZAXmu6Uo5" # EKRAN GÖRÜNTÜNÜZDEKİ TOKEN

# Meta for Developers -> WhatsApp -> API Setup panelindeki "Phone number ID".
PHONE_NUMBER_ID = "806003615919223" # EKRAN GÖRÜNTÜNÜZDEKİ ID

# Mesajların yönlendirileceği, yani en sonunda mesajları okuyacak olan kişinin WhatsApp numarası.
# Ülke koduyla birlikte olmalı (Örn: 99477...).
RECIPIENT_WAID = "994773553356" # SİZİN TEST NUMARANIZ

# --- SON: BİLGİLERİNİZİ BURAYA GİRİN ---


def send_whatsapp_message(message_body):
    """Hedef numaraya formatlanmış mesajı gönderir."""
    
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_WAID,
        "text": {"body": message_body},
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # HTTP 2xx olmayan durumlar için hata fırlatır
        
        print(f"Mesaj başarıyla gönderildi. Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        print(f"Mesaj gönderilirken hata oluştu: {e}")


def whatsapp_webhook(request):
    """
    Meta'dan gelen Webhook isteklerini işleyen ana Cloud Function.
    GET: Webhook doğrulama için.
    POST: Gelen mesajları işlemek için.
    """
    
    # Adım 1: Webhook Doğrulama (GET isteği)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook doğrulaması BAŞARILI.")
            return challenge, 200
        else:
            print("Webhook doğrulaması BAŞARISIZ.")
            return "Verification token mismatch", 403

    # Adım 2: Gelen Mesajları İşleme (POST isteği)
    if request.method == "POST":
        data = request.get_json()
        
        # Gelen verinin yapısını kontrol et ve mesajı ayıkla
        try:
            # Gelen mesaj metnini al
            msg_body = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            
            # Mesajı gönderenin numarasını ve adını al
            from_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            profile_name = data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

            # Yönlendirilecek yeni mesajı formatla
            forwarded_message = (
                f"↘️ YENİ MESAJ ↙️\n\n"
                f"👤 *Gönderen:* {profile_name}\n"
                f"📞 *Numara:* {from_number}\n\n"
                f"📝 *Mesaj:* \n{msg_body}"
            )
            
            print(f"Hazırlanan mesaj: {forwarded_message}")
            
            # Hazırlanan mesajı hedef numaraya gönder
            send_whatsapp_message(forwarded_message)

        except (KeyError, IndexError, TypeError) as e:
            # Eğer gelen veri bir mesaj değilse (örn: okundu bilgisi) veya format farklıysa hata vermemesi için
            print(f"Gelen veri bir metin mesajı değil veya format hatalı: {e}")
            pass

        return "OK", 200

    # Desteklenmeyen bir method gelirse
    return "Unsupported method", 405
