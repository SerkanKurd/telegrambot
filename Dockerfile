# Küçük ve hızlı bir imaj
FROM python:3.13-slim

# Sistem locale vs. ayarlamak opsiyonel
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Çalışma klasörü
WORKDIR /app

# (Varsa) bağımlılıklar -> yoksa bu satır sorun çıkarmaz
COPY requirements.txt* /app/
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Uygulama dosyaları
COPY . /app

# Güvenlik için non-root kullanıcı
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Çalıştırma komutu
CMD ["python", "main.py"]