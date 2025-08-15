# Python'un resmi imajını temel al
FROM python:3.11-slim

# Kodun çalışacağı dizini ayarla
WORKDIR /app

# Önce bağımlılıkları kopyala ve kur (bu, katman önbelleklemesini optimize eder)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Geri kalan tüm proje dosyalarını kopyala
COPY . .

# Cloud Run'ın iletişim kuracağı portu belirt. Bu port ortam değişkeniyle verilir.
# Genellikle 8080 kullanılır.
ENV PORT 8080

# Container başladığında çalıştırılacak komut.
# Flask'in kendi sunucusu geliştirme içindir, bu yüzden production için gunicorn kullanılır.
# ... (Dockerfile'ın üst kısımları) ...

# Cloud Run'ın bize verdiği PORT'u kullan
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "main:app"]
