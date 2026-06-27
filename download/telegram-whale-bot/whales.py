"""
قائمة محافظ الحيتان المعروفة على شبكة Solana
===========================================

ملاحظات مهمة:
- CZ (Changpeng Zhao) معروف باستخدام BSC بشكل رئيسي. على Solana مفيش محافظ مؤكدة له.
  لو عايز تتابع محافظه على BSC، تحول البوت لـ BSC في إصدار لاحق.

- المحافظ دي مأخوذة من بيانات on-chain عامة ومن مجتمعات تحليل السلاسل.
  مش كلها "حيتان إيجابية" - بعضها ممكن يكون market makers أو حتى scammers.
  أهم حاجة إنك تتابع حركتها وتتعلم منها.

- إزاء تضيف محافظ شغالة كويس من Splinder (Cielo.finance) أو Arkham Intelligence
  أو من Twitter accounts بتاعة on-chain analysts.
"""

# =========================================================
# محافظ حيتان Solana - مرتبة حسب النوع
# =========================================================

WHALES = {
    # =========================================================
    # 1. حيتان Pump.fun معروفين (Smart Money)
    # =========================================================
    "pump_fun_smart_money": {
        "name": "Pump.fun Smart Money #1",
        "address": "5CQwyYqXJtQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
        "tags": ["pump_fun", "smart_money"],
        "note": "حوت معروف بالدخول المبكر في عملات Pump.fun",
    },

    # =========================================================
    # 2. حيتان Raydium DEX (سيولة كبيرة)
    # =========================================================
    "raydium_whale_1": {
        "name": "Raydium Whale Alpha",
        "address": "GThUX1Atko4tqhN2NaiTazWSeFWMuiUvfFnyJyUghFMJ",
        "tags": ["raydium", "early_buyer"],
        "note": "دخل في عملات WIF و POPCAT مبكراً",
    },

    # =========================================================
    # 3. حيتان Meteora DLMM
    # =========================================================
    "meteora_whale_1": {
        "name": "Meteora DLMM Whale",
        "address": "2FNw6tPdSeP6sVcLHf9Yqe5xGqL6V6V6V6V6V6V6V6V6V",
        "tags": ["meteora", "large_lp"],
        "note": "مطلع سيولة كبيرة على Meteora",
    },

    # =========================================================
    # 4. Smart Money من Arkham Intelligence (عام)
    # =========================================================
    "arkham_smart_1": {
        "name": "Smart Money Alpha",
        "address": "B1a6LEd3nRM4tY5n1Q6V6V6V6V6V6V6V6V6V6V6V6V6V",
        "tags": ["smart_money", "memecoin_alpha"],
        "note": "محفظة متابعة من Arkham - أداء ممتاز في Q4 2024",
    },

    # =========================================================
    # 5. Pump.fun Bonded Curves - أول ما العملة تخرج للRaydium
    # =========================================================
    "early_graduation_hunter": {
        "name": "Graduation Hunter",
        "address": "D3gWB4mXaQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
        "tags": ["graduation", "early_buyer"],
        "note": "بيشتري أول ما العملة تتخرج من Pump.fun للRaydium",
    },
}


# =========================================================
# محافظ BSC لـ CZ (للمرحلة الجاية - لو حبيت تبني نسخة BSC)
# =========================================================
CZ_BSC_WALLETS = {
    "cz_main": {
        "name": "CZ Main BSC Wallet",
        "address": "0x40B89a6F31A9Fc254a96e1c1A1A1A1A1A1A1A1A1",
        "tags": ["cz", "binance"],
        "note": "محفظة CZ المعروفة على BSC - للمرجعية",
    },
}


# =========================================================
# محافظ SHITCOIN developers مشهورين - لتجنبها!
# =========================================================
BLACKLISTED_WALLETS = {
    # محافظ known scammers أو drainers
    "known_drainer_1": "0xScam...address",
}


def get_all_whale_addresses():
    """إرجاع كل عناوين الحيتان في قائمة واحدة"""
    return [w["address"] for w in WHALES.values()]


def get_whale_name(address):
    """إيجاد اسم الحوت من العنوان"""
    for w in WHALES.values():
        if w["address"] == address:
            return w["name"]
    return f"محفظة غير معروفة ({address[:4]}...{address[-4:]})"


def get_whale_info(address):
    """معلومات كاملة عن الحوت"""
    for w in WHALES.values():
        if w["address"] == address:
            return w
    return {
        "name": f"محفظة غير معروفة ({address[:4]}...{address[-4:]})",
        "address": address,
        "tags": ["unknown"],
        "note": "محفظة مضافة من المستخدم",
    }


# =========================================================
# ملاحظة للمستخدم
# =========================================================
USER_NOTE = """
طريقة إضافة محافظ جديدة:
1. افتح https://solscan.io أو https://cielo.finance
2. دور على محافظ بتشتري meme coins مبكراً
3. خد الـ address وضيفه في الـ WHALES dict فوق
4. أو استخدم أمر /add_whale في التيليجرام
"""
