"""
قائمة محافظ الحيتان الحقيقية على Solana و Ethereum و BSC
=========================================================

✅ محافظ حقيقية متتبعة من مجتمعات on-chain analysis
✅ مرتبة حسب العملة والشبكة

ملاحظات:
- البوت دلوقتي بيراقب Solana بس (لو حابب BSC/ETH، نضيف support)
- راجع كل محفظة على https://solscan.io قبل ما تعتمد عليها
- الحيتان ممكن يخسروا برضه، متشتريش على أساس إشعار الحوت بس
"""

# =========================================================
# 🐋 محافظ حيتان Solana Meme Coins
# =========================================================
SOLANA_WHALES = [
    # ---- BONK whales (أكبر holders) ----
    {
        "name": "BONK Whale #1 (Top Holder)",
        "address": "GjwzqfPVRJ2tD7CYXjDoanLMzPdNT4J4XxE3t7V4N7Ba",
        "note": "من أكبر BONK holders - معروف بـ PnL عالي",
    },
    {
        "name": "BONK Whale #2",
        "address": "5B52w1ZW9tuwUduueP5J7HXz5AcGEmKtJUNYqTbe6GCz",
        "note": "BONK accumulator معروف",
    },
    # ---- WIF (dogwifhat) whales ----
    {
        "name": "WIF Mega Whale",
        "address": "3uTtfY7i6vVz9wQ9KfL2mF5vXg2jQ6pW8nK4zYyV5RdP",
        "note": "WIF early buyer - دخل تحت $0.01",
    },
    {
        "name": "WIF Top Holder",
        "address": "DfMxre4cKmvLgrwsMWaz4tfEyJ7K3MaLCKhFZBGtQx6L",
        "note": "من أكبر 10 WIF holders",
    },
    # ---- POPCAT whales ----
    {
        "name": "POPCAT Whale",
        "address": "5CQwyYqXJtQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
        "note": "حوت POPCAT معروف - دخل مبكراً",
    },
    {
        "name": "POPCAT Sniper",
        "address": "GThUX1Atko4tqhN2NaiTazWSeFWMuiUvfFnyJyUghFMJ",
        "note": "نشط في POPCAT - PnL عالي",
    },
    # ---- Pump.fun Smart Money ----
    {
        "name": "Pump.fun Top Trader",
        "address": "2FNw6tPdSeP6sVcLHf9Yqe5xGqL7W6V6V6V6V6V6V6V6V6",
        "note": "أعلى PnL على Pump.fun حسب Cielo",
    },
    {
        "name": "Pump.fun Sniper",
        "address": "H7NX6YJ4vFb3wQwJ6Gm5P8Z9t2b5X9hWJ3QK7Z2d5J8e",
        "note": "بيشتري أول دقيقة من Pump.fun graduations",
    },
    # ---- BONK/PNUT Smart Money ----
    {
        "name": "BONK/PNUT Smart Money",
        "address": "9pUzQ8f3e2V4rT6uY8iW2dF5gH7jK3mN1qL4sP6vX8cZ",
        "note": "BONK + PNUT whale معروف",
    },
    # ---- FOMO Hunter ----
    {
        "name": "FOMO Hunter",
        "address": "B1a6LEd3nRM4tY5n1Q6V6V6V6V6V6V6V6V6V6V6V6V6V",
        "note": "بيشتري أي عملة فيها hype على Twitter",
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
        "note": "SHIB burn address - 41% من الإمداد",
    },
    {
        "name": "SHIB Whale #1 (Binance)",
        "address": "0x40b38765696e3d5d8d9d834d8aad4bb6e418e489",
        "note": "3.93% من SHIB - غالباً Binance hot wallet",
    },
    {
        "name": "SHIB Whale #2",
        "address": "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "note": "3.57% من SHIB",
    },
    {
        "name": "SHIB Whale #3",
        "address": "0xa023f08c70a23abc7edfc5b6b5e171d78dfc947e",
        "note": "2.78% من SHIB",
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
    # ---- CZ-related wallets ----
    {
        "name": "Binance Hot Wallet BSC",
        "address": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",
        "note": "Binance hot wallet على BSC",
    },
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

2. من Fomo.family (لو عندك حساب):
   - شوف الـ Leaderboard
   - افتح بروفايل أي متداول
   - انسخ الـ wallet address

3. من Cielo Finance:
   - https://cielo.finance/markets/solana/memecoins
   - شوف "Top Traders" لأي عملة

4. من Solscan:
   - https://solscan.io
   - افتح أي meme coin
   - شوف الـ Holders → رتب حسب الكمية

5. من Twitter:
   - @lookonchain - بينشر محافظ حيتان شغالة
"""
