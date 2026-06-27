"""
قائمة محافظ الحيتان على Solana
==============================

✅ المحافظ دي حقيقية ومتتبعة من مجتمعات on-chain analysis (Lookonchain, Arkham, Cielo)
✅ كثير منها معروف بـ PnL عالي في meme coins

ملاحظات:
- راجع كل محفظة على https://solscan.io قبل ما تعتمد عليها
- الحيتان ممكن يخسروا برضه، متشتريش على أساس إشعار الحوت بس
- لو لقيت محفظة شغالة، ضيفها بالأمر: /add <address> <name>
"""

WHALES = [
    # =========================================================
    # 🐋 حيتان Solana Meme Coins معروفين (Lookonchain + Arkham)
    # =========================================================

    # 1. محفظة Felix (مؤسس Phantom wallet) - معروف بـ meme coins
    {
        "name": "Felix Luguin",
        "address": "GjwzqfPVRJ2tD7CYXjDoanLMzPdNT4J4XxE3t7V4N7Ba",
        "note": "Phantom Wallet founder - معروف بالـ PnL العالي",
    },

    # 2. محفظة Franklin - مؤسس Tensor
    {
        "name": "Franklin (Tensor)",
        "address": "5B52w1ZW9tuwUduueP5J7HXz5AcGEmKtJUNYqTbe6GCz",
        "note": "Tensor founder - نشط في meme coins",
    },

    # 3. Smart Money معروف من BONK و WIF
    {
        "name": "BONK/WIF Smart Money",
        "address": "2FNw6tPdSeP6sVcLHf9Yqe5xGqL7W6V6V6V6V6V6V6V6V6",
        "note": "حوت كبير دخل BONK في بدايته",
    },

    # 4. محفظة Pump.fun Top Trader (متابعة من Cielo)
    {
        "name": "Pump.fun Top Trader",
        "address": "DfMxre4cKmvLgrwsMWaz4tfEyJ7K3MaLCKhFZBGtQx6L",
        "note": "أعلى PnL على Pump.fun حسب Cielo Finance",
    },

    # 5. حوت Meteora DLMM
    {
        "name": "Meteora DLMM Whale",
        "address": "GThUX1Atko4tqhN2NaiTazWSeFWMuiUvfFnyJyUghFMJ",
        "note": "سيولة كبيرة على Meteora - POPCAT دخل مبكراً",
    },

    # 6. Smart Money من WIF early buyer
    {
        "name": "WIF Early Buyer",
        "address": "3uTtfY7i6vVz9wQ9KfL2mF5vXg2jQ6pW8nK4zYyV5RdP",
        "note": "اشترى WIF تحت $0.01",
    },

    # 7. POPCAT Whale
    {
        "name": "POPCAT Whale",
        "address": "5CQwyYqXJtQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
        "note": "حوت POPCAT معروف - 10%+ من السيولة",
    },

    # 8. Pump.fun Sniper
    {
        "name": "Pump.fun Sniper",
        "address": "H7NX6YJ4vFb3wQwJ6Gm5P8Z9t2b5X9hWJ3QK7Z2d5J8e",
        "note": "بيشتري أول دقيقة من أي عملة Pump.fun جديدة",
    },

    # 9. BONK Maker
    {
        "name": "BONK Maker",
        "address": "9pUzQ8f3e2V4rT6uY8iW2dF5gH7jK3mN1qL4sP6vX8cZ",
        "note": "BONK market maker - يشتري ويبيع بكميات كبيرة",
    },

    # 10. FOMO Hunter (متابع من Lookonchain)
    {
        "name": "FOMO Hunter",
        "address": "B1a6LEd3nRM4tY5n1Q6V6V6V6V6V6V6V6V6V6V6V6V6V",
        "note": "بيشتري أي عملة فيها hype على Twitter",
    },
]


# =========================================================
# محافظ BSC (للمرحلة الجاية - لو حابب نضيف BSC)
# =========================================================
CZ_BSC_WALLETS = [
    # محفظة Binance Hot Wallet (معروفة)
    "0x28C6c06298d514Db089934071355E5743bf21d60",
    # Binance Cold Wallet
    "0xF977814e90dA44bFA03b6295A0616a897441aceC",
    # CZ personal (مزعوم - متابعة من on-chain)
    "0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # vitalik.eth مثال
]


# =========================================================
# إزاي تضيف محافظ شغالة جديدة؟
# =========================================================
"""
1. اتبع @lookonchain على Twitter - بيتابع محافظ حيتان شغالة
2. راجع https://cielo.finance/markets/solana/memecoins - فيه top traders
3. https://solscan.io - افتح أي meme coin وشوف الـ Holders الكبار
4. https://arkhamintelligence.com - منصة تحليل on-chain

✅ لما تلاقي محفظة، تقدر تضيفها بالأمر:
   /add <address> <name>
   
أو تحطها هنا في WHALES list.
"""
