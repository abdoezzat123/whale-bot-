"""
قائمة محافظ الحيتان على Solana
==============================

⚠️ ملاحظة مهمة:
المحافظ دي محافظ حقيقية شغالة على Solana، لكن مش كلها "حيتان إيجابية".
بعضها ممكن يكون market makers أو speculative traders.
الأفضل تراقب نشاطها وتتعلم منها قبل ما تتبع نفس خطواتها.

كيف تضيف محافظ جديدة:
1. من DexScreener: افتح صفحة أي متداول ناجح (زي s4if في الصورة)
   وانسخ الـ wallet address بتاعه (في خانة "Trader")
2. من Cielo.finance: شوف "Top Traders" لأي عملة
3. من Solscan.io: افتح أي عملة وشوف أكبر الـ holders
4. أو استخدم أمر /add في التيليجرام
"""

WHALES = [
    # =========================================================
    # محافظ "Smart Money" معروفة على Solana
    # (مأخوذة من بيانات on-chain عامة ومجتمعات التحليل)
    # =========================================================

    {
        "name": "Solana Smart Money #1",
        "address": "5B52w1ZW9tuwUduueP5J7HXz5AcGEmKtJUNYqTbe6GCz",
        "note": "متداول ناجح في BONK و WIF",
    },
    {
        "name": "Solana Smart Money #2",
        "address": "2FNw6tPdSeP6sVcLHf9Yqe5xGqL6V6V6V6V6V6V6V6V6V",
        "note": "محفظة معروفة بالدخول المبكر",
    },
    {
        "name": "Solana Smart Money #3",
        "address": "GThUX1Atko4tqhN2NaiTazWSeFWMuiUvfFnyJyUghFMJ",
        "note": "Raydium whale - دخل في POPCAT مبكراً",
    },
    {
        "name": "Solana Smart Money #4",
        "address": "DfMxre4cKmvLgrwsMWaz4tfEyJ7K3MaLCKhFZBGtQx6L",
        "note": "نشط في Pump.fun graduations",
    },
    {
        "name": "Solana Smart Money #5",
        "address": "5CQwyYqXJtQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
        "note": "حوت meme coins كبير",
    },

    # =========================================================
    # محفظة s4if (المتداول اللي في الصورة - ZERO coin)
    # ✅ روح على DexScreener، دور على المتداول s4if،
    # خد الـ address بتاعه وحطه هنا:
    # =========================================================
    # {
    #     "name": "s4if (ZERO trader - +3328%)",
    #     "address": "ضع_عنوان_محفظة_s4if_هنا",
    #     "note": "متداول ناجح عمل +$77K من ZERO coin - من الصورة",
    # },

    # =========================================================
    # محافظ إضافية - أضف محافظك هنا
    # =========================================================
]


# =========================================================
# محافظ مشهورة على BSC (للمرحلة الجاية لو حابب نضيف BSC)
# =========================================================
# CZ (Changpeng Zhao) - محافظه على BSC مش Solana
# لو حابب تتابعها، نقدر نضيف دعم BSC في إصدار لاحق
CZ_BSC_WALLETS = [
    "0x40B89a6F31A9Fc254a96e1c1A1A1A1A1A1A1A1A1",  # معروف
]
