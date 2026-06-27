"""
إعدادات البوت
=============
يقرأ القيم من ملف .env ويوفرها للبوت كله.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # === Helius (Solana RPC) ===
    HELIUS_API_KEY: str = os.getenv("HELIUS_API_KEY", "")
    HELIUS_RPC_URL: str = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    HELIUS_API_URL: str = f"https://api.helius.xyz"

    # === DexScreener (مجاني 100%) ===
    DEXSCREENER_API: str = "https://api.dexscreener.com"

    # === إعدادات الإشعارات ===
    MIN_TX_VALUE_USD: float = float(os.getenv("MIN_TX_VALUE_USD", "1000"))
    WHALE_ACCUMULATION_THRESHOLD: int = int(os.getenv("WHALE_ACCUMULATION_THRESHOLD", "3"))
    WHALE_ACCUMULATION_WINDOW_HOURS: int = int(os.getenv("WHALE_ACCUMULATION_WINDOW_HOURS", "6"))
    EARLY_ENTRY_HOURS: int = int(os.getenv("EARLY_ENTRY_HOURS", "24"))

    # === فترات العمل ===
    SUMMARY_INTERVAL_HOURS: int = int(os.getenv("SUMMARY_INTERVAL_HOURS", "6"))
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))

    # === قاعدة البيانات ===
    DB_PATH: str = "whale_tracker.db"

    @classmethod
    def validate(cls) -> list:
        """التحقق من وجود كل القيم المطلوبة - إرجاع قائمة بالأخطاء"""
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN or "ضع_" in cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN غير موجود في .env")
        if not cls.TELEGRAM_CHAT_ID or "ضع_" in cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID غير موجود في .env")
        if not cls.HELIUS_API_KEY or "ضع_" in cls.HELIUS_API_KEY:
            errors.append("HELIUS_API_KEY غير موجود في .env")
        return errors


config = Config()
