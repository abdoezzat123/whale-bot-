# 🐋 بوت تتبع حيتان Meme Coins على Solana

بوت بسيط بيراقب محافظ الحيتان على شبكة Solana وبيبعتلك إشعار فوري على Telegram لما أي حوت يشتري meme coin.

## ✨ المميزات

- ✅ **مجاني 100%** - مش محتاج أي API key (يستخدم public Solana RPCs)
- ✅ إشعار فوري عند شراء أي حوت
- ✅ بيانات العملة الكاملة من DexScreener (السعر، السيولة، الحجم، Market Cap)
- ✅ كشف العملات الجديدة (🆕 جديده!)
- ✅ فلترة حسب قيمة الشراء (مثلاً إشعار بس للشركات فوق $500)
- ✅ إضافة/حذف محافظ من Telegram مباشرة
- ✅ **Multi-RPC system** - بيستخدم عدة endpoints بالتوازي علشان reliability أعلى
- ✅ لو حطيت Helius API key (اختياري) → أسرع وأقوى

## 🚀 التشغيل السريع (Docker - موصى به)

### على AWS EC2 / أي VPS:

```bash
# 1. انسخ المشروع
git clone https://github.com/USERNAME/whale-bot.git
cd whale-bot

# 2. املأ .env (التوكن موجود بالفعل - بس ضيف Helius لو عندك)
nano .env

# 3. شغّل بـ Docker
docker compose up -d --build

# 4. شوف الـ logs
docker compose logs -f
```

### على جهازك (بدون Docker):

```bash
# 1. ثبّت المتطلبات
python3 -m venv venv
source venv/bin/activate    # ويندوز: venv\Scripts\activate
pip install -r requirements.txt

# 2. املأ .env

# 3. شغّل
python bot.py
```

## 📋 إعداد .env

```env
TELEGRAM_BOT_TOKEN=8688639320:AAHw_CthYwmNDBcYwKnuIbT_MOSAxLrkcCM
TELEGRAM_CHAT_ID=911912421
HELIUS_API_KEY=           # اختياري - لو فاضي، البوت يستخدم public RPCs
MIN_BUY_USD=500
POLL_SECONDS=30
```

## 🎛️ أوامر Telegram

```
/list                      # عرض كل المحافظ المتابعة
/add <address> <name>      # إضافة محفظة
/remove <address>          # حذف محفظة
/stats                     # إحصائيات
/help                      # المساعدة
```

## 🐋 إزاي تلاقي محافظ حيتان شغالة؟

### 1. من Fomo.family (لو عندك حساب)
- شوف الـ Leaderboard
- افتح بروفايل أي متداول
- انسخ الـ wallet address

### 2. من Cielo Finance
- https://cielo.finance/markets/solana/memecoins
- شوف "Top Traders" لأي عملة

### 3. من Solscan
- https://solscan.io
- افتح أي meme coin (مثل KINS, BONK, WIF)
- شوف الـ Holders → رتب حسب الكمية

### 4. من Twitter
- @lookonchain
- @solwhalesbot

## 📊 شكل الإشعار

```
🐋 حوت اشترى!

👤 الحوت: Whale Alpha 1
📝 حوت Pump.fun معروف

🪙 العملة: KINS - Kintara 🆕 جديده! (3 ساعة)
💰 قيمة الشراء: $12,500 (68.4 SOL)
📊 السعر: $0.01403
💧 السيولة: $420,000
📈 الحجم 24h: $870,000
🏷️ Market Cap: $14M
🔗 DEX: pumpswap

🔗 DexScreener | Solscan TX
🏦 المحفظة
```

## 🐳 أوامر Docker

```bash
# تشغيل
docker compose up -d --build

# وقف
docker compose down

# ريستارت
docker compose restart

# logs
docker compose logs -f

# تحديث الكود
git pull && docker compose up -d --build
```

## 🛠️ Multi-RPC System

البوت بيستخدم 5 RPC endpoints بالتوازي:

1. **Solana Official** (api.mainnet-beta.solana.com) - 40 req/sec
2. **Triton Public** (solana-mainnet.rpc.extrnode.com)
3. **Ankr Public** (rpc.ankr.com/solana)
4. **Alchemy Demo** (solana-mainnet.g.alchemy.com)
5. **Helius** (لو حطيت API key) - أقوى وأسرع

لو endpoint وقع، البوت ينتقل تلقائياً للـ التالي. كده البوت مش هيوقف أبداً.

## ⚠️ ملاحظات

1. **Public RPC rate limit**: تقدر تراقب 20-30 محفظة كل 30 ثانية بدون مشاكل
2. **لو حابب تراقب أكتر**: سجل في Helius ($0 للأول 100K ريكوست)
3. **الدقة**: مش كل معاملة هتتبعت كـ "شراء". ممكن بعضها يكون routing معقد
4. **المخاطر**: متشتريش على أساس إشعار الحوت بس. الحيتان بتفشل برضه

## 📁 ملفات المشروع

```
whale-bot/
├── bot.py              # الكود الرئيسي
├── whales.py           # قائمة المحافظ الافتراضية
├── requirements.txt    # متطلبات Python
├── Dockerfile          # لتشغيل Docker
├── docker-compose.yml  # إعدادات Docker
├── .env                # إعداداتك (سرّي!)
└── README.md           # هذا الملف
```

## 🆘 استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| البوت شغال بس مفيش إشعارات | تأكد إن المحافظ فيها نشاط (شوفها على solscan.io) |
| Rate limit من RPC | زود `POLL_SECONDS` لـ 60 أو سجل في Helius |
| إشعارات بطيئة | قلل `POLL_SECONDS` لـ 15 أو أضف Helius |
| Docker مش شغال | `docker compose logs` للتشخيص |
