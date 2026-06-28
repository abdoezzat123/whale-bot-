FROM python:3.11-slim

# تحديث النظام وتثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات أولاً (للتخزين المؤقت)
COPY requirements.txt .

# تثبيت متطلبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY bot.py bsc_monitor.py whales.py ./

# إنشاء مجلد للبيانات
RUN mkdir -p /app/data

# متغيرات البيئة الافتراضية (تتعدل من .env أو docker run -e)
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""
ENV HELIUS_API_KEY=""
ENV MIN_BUY_USD="500"
ENV POLL_SECONDS="30"
ENV DB_PATH="/app/data/seen.db"

# تشغيل البوت
CMD ["python", "-u", "bot.py"]
