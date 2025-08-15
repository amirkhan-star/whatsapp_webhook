import os
import requests
import json
from flask import Flask, request
from google.cloud import secretmanager

# --- GÜVENLİ KURULUM: GİZLİ BİLGİLERİ SECRET MANAGER'DAN ÇEKME ---

# Google Cloud ortam değişkeninden proje ID'sini al
PROJECT_ID = os.environ.get('GCP_PROJECT')

# Secret Manager istemcisini başlat
client = secretmanager.SecretManagerServiceClient()

def access_secret_version(secret_id, version_id="latest"):
    """Secret Manager'dan bir gizli bilginin değerini alır."""
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Cloud Function başlatılırken gizli bilgileri bir kereye mahsus çek ve değişkenlere ata
# Bu sayede her istekte tekrar tekrar çekilmez, daha verimli çalışır.
try:
    ACCESS_TOKEN = access_secret_version("whatsapp-access-token")
    VERIFY_TOKEN = access_secret_version("whatsapp-verify-token")
    PHONE_NUMBER_ID = access_secret_version("whatsapp-phone-number-id")
    RECIPIENT_WAID = access_secret_version("whatsapp-recipient-waid")
    print("Tüm gizli bilgiler Secret Manager'dan başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Secret Manager'dan bilgiler yüklenemedi! İzinleri kontrol edin. Detay: {e}")
    # Hata durumunda fonksiyonun çalışmasını engellemek için boş değerler ata
    ACCESS_TOKEN, VERIFY_TOKEN, PHONE_NUMBER_ID, RECIPIENT_WAID = None, None, None, None


# --- OTOMASYON MANTIĞI (DEĞİŞİKLİK YOK) ---

def send_whatsapp_message(message_body):
    """Hedef numaraya formatlanmış mesajı gönderir."""
    if not all([ACCESS_TOKEN, PHONE_NUMBER_ID, RECIPIENT_WAID]):
        print("HATA: Gönderim için gerekli gizli bilgiler eksik. Fonksiyon durduruldu.")
        return

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": RECIPIENT_WAID, "text": {"body": message_body}}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print(f"Mesaj başarıyla gönderildi. Status: {response.status_code}, Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Mesaj gönderilirken hata oluştu: {e}")


def whatsapp_webhook(request):
    """Meta'dan gelen Webhook isteklerini işleyen ana Cloud Function."""
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            print("Webhook doğrulaması BAŞARILI.")
            return request.args.get("hub.challenge"), 200
        else:
            print("Webhook doğrulaması BAŞARISIZ.")
            return "Verification token mismatch", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            msg_body = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            from_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            profile_name = data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

            forwarded_message = (
                f"↘️ YENİ MESAJ ↙️\n\n"
                f"👤 *Gönderen:* {profile_name}\n"
                f"📞 *Numara:* {from_number}\n\n"
                f"📝 *Mesaj:* \n{msg_body}"
            )
            
            send_whatsapp_message(forwarded_message)
        except (KeyError, IndexError, TypeError):
            pass # Gelen veri metin mesajı değilse sessizce geç
        return "OK", 200

    return "Unsupported method", 405
