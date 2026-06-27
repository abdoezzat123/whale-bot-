# 🐋 بوت تتبع حيتان Meme Coins على Solana

بوت بسيط بيراقب محافظ الحيتان على شبكة Solana وبيبعتلك إشعار فوري على Telegram لما أي حوت يشتري meme coin.

## المميزات

- ✅ إشعار فوري عند شراء أي حوت
- ✅ بيانات العملة الكاملة من DexScreener (السعر، السيولة، الحجم، Market Cap)
- ✅ كشف العملات الجديدة (🆕 جديده!)
- ✅ فلترة حسب قيمة الشراء (مثلاً إشعار بس للشركات فوق $500)
- ✅ إضافة/حذف محافظ من Telegram مباشرة
- ✅ مجاني 100% (Helius free tier + DexScreener free)

## المتطلبات

- Python 3.9+
- Telegram Bot Token (من @BotFather)
- Helius API key (مجاني من https://www.helius.dev/)
- Chat ID بتاعك على Telegram

## التشغيل

### 1. تثبيت المتطلبات

```bash
cd telegram-whale-bot
python3 -m venv venv
source venv/bin/activate    # على ويندوز: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. ضبط الإعدادات

افتح ملف `.env` واملأ القيم:

```env
TELEGRAM_BOT_TOKEN=8688639320:AAHw_CthYwmNDBcYwKnuIbT_MOSAxLrkcCM  # ✅ موجود
TELEGRAM_CHAT_ID=123456789        # ← تحتاج تجيبه
HELIUS_API_KEY=                   # ← تحتاج تسجل في helius.dev
MIN_BUY_USD=500
POLL_SECONDS=30
```

### 3. الحصول على Telegram Chat ID

1. ابدأ محادثة مع البوت على Telegram وابعث `/start`
2. افتح @userinfobot على Telegram وابعث أي رسالة
3. هيبعتلك الـ ID بتاعك (رقم زي `123456789`)

### 4. الحصول على Helius API Key

1. روح https://www.helius.dev/
2. اعمل Sign up (مجاني)
3. اعمل Dashboard → APIs → Create API Key
4. انسخ الـ key وحطه في `.env`

### 5. تشغيل البوت

```bash
python bot.py
```

هتلاقي رسالة على Telegram بتأكد إن البوت اشتغل ✅

## إدارة المحافظ

من Telegram مباشرة:

```
/list                      # عرض كل المحافظ
/add <address> <name>      # إضافة محفظة
/remove <address>          # حذف محفظة
/stats                     # إحصائيات
/help                      # المساعدة
```

ولإضافة محافظ افتراضية دائمة، عدل ملف `whales.py`.

## إزاي تلاقي محافظ حيتان شغالة؟

### الطريقة الأسهل: Cielo Finance
1. روح https://cielo.finance
2. افتح "Memes" → "Top Traders" على Solana
3. شوف المحافظ اللي عندها PnL عالي في آخر 7 أيام
4. انسخ الـ address وضيفه بالأمر `/add`

### من Solscan
1. روح https://solscan.io
2. افتح أي عملة meme coin (مثلاً BONK أو WIF)
3. شوف الـ Holders → رتب حسب الكمية
4. المحافظ الكبيرة (1%+) = حيتان

### من Twitter
حسابات بتتابع محافظ الحيتان:
- @lookonchain
- @scam_sniffer (لكن ده للـ scams)
- @solwhalesbot

## شكل الإشعار

```
🐋 حوت اشترى!

👤 الحوت: Whale Alpha 1
📝 حوت Pump.fun معروف

🪙 العملة: PEPE - Pepe Coin 🆕 جديده! (3 ساعة)
💰 قيمة الشراء: $12,500 (68.4 SOL)
📊 السعر: $0.00000123
💧 السيولة: $245,000
📈 الحجم 24h: $1.2M
🏷️ Market Cap: $5.4M
🔗 DEX: raydium

🔗 DexScreener | Solscan TX
🏦 المحفظة
```

## استضافة البوت 24/7

### الخيار 1: على جهازك (بسيط)
شغله وخلينه شغال. لو القفل، البوت يقف.

### الخيار 2: VPS (موصى به)
أي VPS رخيص:
- **Hetzner CX11**: €3.29/شهر (موصى به)
- **DigitalOcean Droplet**: $4/شهر
- **Vultr**: $2.5/شهر

```bash
# على VPS
git clone <repo>
cd telegram-whale-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تشغيل بـ tmux علشان يفضل شغال حتى بعد القفل
tmux new -s whale
python bot.py
# Ctrl+B ثم D للخروج من الـ tmux
```

### الخيار 3: systemd (للتشغيل التلقائي بعد الإعادة)
```bash
sudo nano /etc/systemd/system/whale-bot.service
```
```ini
[Unit]
Description=Whale Tracker Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-whale-bot
ExecStart=/home/ubuntu/telegram-whale-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable whale-bot
sudo systemctl start whale-bot
sudo systemctl status whale-bot  # للتأكد
```

## ملاحظات مهمة

1. **Helius Free Tier**: 100K ريكوست شهرياً. كل فحص لمحفظة بياخد ~6-7 ريكسات، يعني 50 محفظة كل 30 ثانية = ~720K ريكس/يوم. **لو هتابع كتير، ترقية لـ $49/شهر**.

2. **الدقة**: مش كل معاملة هتتبعت كـ "شراء". ممكن بعضها يكون routing معقد من Jupiter. لو لقيت إشعارات غلط، ارفع `MIN_BUY_USD`.

3. **المخاطر**: متشتريش على أساس إشعار الحوت بس. الحيتان بتفشل برضه. اعمل بحثك.

4. **التوكن في `.env`**: متشاركوش مع حد ومترفعهوش على GitHub.

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| "TELEGRAM_CHAT_ID غير موجود" | ابدأ محادثة مع البوت وبعت /start، ثم استخدم @userinfobot |
| "HELIUS_API_KEY غير موجود" | سجل في helius.dev وانسخ الـ key |
| البوت شغال بس مفيش إشعارات | تأكد إن المحافظ بتاعة الحيتان فيها نشاط (شوفها على solscan.io) |
| إشعارات بطيئة | قلل `POLL_SECONDS` لـ 15 |
| كتير Rate limit من Helius | زود `POLL_SECONDS` أو رقّي خطة Helius |

## ملفات المشروع

```
telegram-whale-bot/
├── bot.py              # الكود الرئيسي
├── whales.py           # قائمة المحافظ الافتراضية
├── requirements.txt    # متطلبات Python
├── .env                # إعداداتك (سرّي!)
└── README.md           # هذا الملف
```

## الخطوة الجاية (اختياري)

لو حابب توسع البوت:
- إضافة تنبيهات التجميع (3 حيتان يشتروا نفس العملة في 6 ساعات = 🔥 تجميع)
- دعم BSC (لمحافظ CZ)
- إضافة RPC backup لو Helius وقع
- تحليل PnL للحوت (هل هو رابح في آخر صفقاته؟)
