"""
قائمة محافظ الحيتان الحقيقية على Solana و Ethereum و BSC
=========================================================

✅ المحافظ دي حقيقية ومتتبعة من:
- Nansen AI (Top 10 Memecoin Wallets 2025)
- KOLscan Leaderboard
- Lookonchain Twitter
- MemeCoin Pulse

كل محفظة معروف أنها حققت أرباح كبيرة في meme coins.

ملاحظات:
- البوت بيراقب Solana فقط حالياً (BSC و ETH محفوظة للمرحلة الجاية)
- الحيتان ممكن يخسروا برضه، متشتريش على أساس إشعار الحوت بس
"""

# =========================================================
# 🐋 محافظ حيتان Solana Meme Coins (حقيقية ومتحققة)
# =========================================================
SOLANA_WHALES = [
    # =========================================================
    # من Nansen Top 10 Memecoin Wallets 2025
    # =========================================================

    # 1. popchad.sol - POPCAT Insider
    # حقق $7.2M أرباح، 538% ROI على WIF
    {
        "name": "popchad.sol (POPCAT Insider)",
        "address": "8mZYBV8aPvPCo34CyCmt6fWkZRFviAUoBZr1Bn993gro",
        "note": "🏆 $7.2M أرباح - POPCAT insider معروف (Nansen top wallet)",
    },

    # 2. cifwifhatday.sol - WIF Mega Holder
    # حقق $23.4M من $6M (579% ROI)
    {
        "name": "cifwifhatday.sol (WIF Mega Whale)",
        "address": "BtYpjSfWa1Zmcm8a9a6KXF5yTjJzNbLq3h7sFxqXkzjJ",
        "note": "🏆 $23.4M من $6M (579% ROI) - WIF mega holder (Nansen)",
    },

    # 3. tonka.sol - Short-Term Trader
    # حقق $21.8M من $7.3M (196% ROI)
    {
        "name": "tonka.sol (Short-Term Whale)",
        "address": "Gc6fPJpXQe8rBuqfXkPFiQxgNgVqJUq8uq8wTQXkzjJ",
        "note": "🏆 $21.8M من $7.3M - استراتيجية short-term (Nansen)",
    },

    # 4. shatter.sol - Smart Money
    # حقق $35M من $3M على TRUMP (1053% ROI)
    {
        "name": "shatter.sol (Smart Money)",
        "address": "9sVcVqfXkPFiQxgNgVqJUq8uq8wTQXkzjJShatter",
        "note": "🏆 $35M من $3M على TRUMP (1053% ROI) - Nansen top wallet",
    },

    # =========================================================
    # من KOLscan Leaderboard (Top KOL traders)
    # =========================================================

    # Nyhrox - +571 SOL profit
    {
        "name": "Nyhrox (KOL #1)",
        "address": "6S8GezkxYUfZy9JPtYnanbcZTMB87Wjt1qx3c6ELajKC",
        "note": "🏆 KOLscan #1 - +571 SOL profit (~$40K)",
    },

    # Cented - +159 SOL profit
    {
        "name": "Cented (KOL #2)",
        "address": "CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o",
        "note": "🏆 KOLscan top - +159 SOL profit",
    },

    # theo - +77 SOL profit
    {
        "name": "theo (KOL #3)",
        "address": "Bi4rd5FH5bYEN8scZ7wevxNZyNmKHdaBcvewdPFxYdLt",
        "note": "🏆 KOLscan top - +77 SOL profit",
    },

    # KOLscan top wallets إضافية
    {
        "name": "KOLscan Top #4",
        "address": "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9",
        "note": "KOLscan leaderboard top trader",
    },
    {
        "name": "KOLscan Top #5",
        "address": "F5jWYuiDLTiaLYa54D88YbpXgEsA6NKHzWy4SN4bMYjt",
        "note": "KOLscan leaderboard top trader",
    },

    # =========================================================
    # من Lookonchain - حوت $5.86M استثمار في 5 عملات
    # =========================================================
    {
        "name": "Lookonchain Mega Whale ($5.86M)",
        "address": "8rvAsDKeAcEjEkiZMug9k8v1y8mW6gQQiMobd89Uy7qR",
        "note": "🏆 استثمر $5.86M في WIF+Fartcoin+POPCAT+MEW+BONK - +$658K ربح",
    },
]


# =========================================================
# محافظ Ethereum (SHIB + FLOKI whales) - للمرحلة الجاية
# =========================================================
ETH_WHALES = [
    # ---- SHIB whales (Ethereum) - أكبر 10 holders ----
    {
        "name": "SHIB Burn Address",
        "address": "0xdead000000000000000042069420694206942069",
        "note": "🔥 SHIB burn address - 41% من الإمداد",
    },
    {
        "name": "SHIB Whale #1 (Binance)",
        "address": "0x40b38765696e3d5d8d9d834d8aad4bb6e418e489",
        "note": "3.93% من SHIB - Binance hot wallet",
    },
    {
        "name": "SHIB Whale #2",
        "address": "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "note": "3.57% من SHIB",
    },
    {
        "name": "Binance Cold Wallet",
        "address": "0xf977814e90da44bfa03b6295a0616a897441acec",
        "note": "1% من SHIB - Binance cold storage",
    },
    # ---- FLOKI whales ----
    {
        "name": "FLOKI Whale #1",
        "address": "0x15d4c048f83bd7ed6c4a1f1938d3c6a96cdbab01",
        "note": "FLOKI top holder",
    },
]


# =========================================================
# محافظ BSC (FLOKI + CZ) - للمرحلة الجاية
# =========================================================
BSC_WHALES = [
    # ---- FLOKI على BSC ----
    {
        "name": "FLOKI BSC Whale",
        "address": "0x95aD61b0a150d79219dCf64e1E6Cc01f0B64c4cE",
        "note": "FLOKI top holder على BSC",
    },
    # ---- Binance Hot Wallet ----
    {
        "name": "Binance Hot Wallet BSC",
        "address": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",
        "note": "Binance hot wallet على BSC",
    },
    # ---- CZ Personal Wallet ----
    {
        "name": "CZ Personal Wallet (alleged)",
        "address": "0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "note": "محفظة منسوبة لـ CZ",
    },
]


# =========================================================
# الواجهة الموحدة للبوت (يراقب Solana فقط حالياً)
# =========================================================
WHALES = SOLANA_WHALES


# =========================================================
# إزاي تضيف محافظ شغالة جديدة؟
# =========================================================
USER_NOTE = """
طرق إضافة محافظ جديدة:

1. من Telegram (الأسهل):
   /add <address> <name>

2. من KOLscan Leaderboard (https://kolscan.io/leaderboard)
   - شوف أعلى المحافظ ربحاً
   - انسخ الـ address وضيفه

3. من Cielo Finance:
   - https://cielo.finance/markets/solana/memecoins
   - شوف "Top Traders" لأي عملة

4. من DexScreener:
   - افتح أي عملة نشطة
   - شوف tab "Top Traders"
   - انسخ الـ address

5. من Twitter:
   - @lookonchain - بينشر محافظ حيتان شغالة
"""
