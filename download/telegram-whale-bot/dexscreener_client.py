"""
عميل DexScreener API
====================
DexScreener مجاني 100% وبيقدم:
- معلومات العملة (السعر، السيولة، حجم التداول)
- وقت إنشاء الـ pair (مهم لكشف الدخول المبكر!)
- روابط السوشيال والموقع

الـ API: https://api.dexscreener.com
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)


class DexScreenerClient:
    BASE_URL = "https://api.dexscreener.com"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """
        جلب معلومات عملة من DexScreener.
        بيرجع dict فيه:
        - symbol, name
        - price_usd
        - liquidity_usd
        - volume_24h
        - market_cap
        - pair_created_at (timestamp)
        - dex_id (raydium, meteora, pump_fun, etc.)
        - social_links
        """
        url = f"{self.BASE_URL}/tokens/v1/solana/{token_address}"
        session = await self.get_session()
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"DexScreener {resp.status} for {token_address}")
                    return None
                pairs = await resp.json()
                if not pairs:
                    return None

                # نختار الـ pair الأكبر سيولة
                best_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))

                # نجمع البيانات
                info = {
                    "token_address": token_address,
                    "symbol": best_pair.get("baseToken", {}).get("symbol", "???"),
                    "name": best_pair.get("baseToken", {}).get("name", "Unknown"),
                    "price_usd": float(best_pair.get("priceUsd", 0) or 0),
                    "liquidity_usd": float(best_pair.get("liquidity", {}).get("usd", 0) or 0),
                    "volume_24h": float(best_pair.get("volume", {}).get("h24", 0) or 0),
                    "market_cap": float(best_pair.get("fdv", 0) or 0),
                    "pair_created_at": best_pair.get("pairCreatedAt"),
                    "dex_id": best_pair.get("dexId", "unknown"),
                    "pair_address": best_pair.get("pairAddress"),
                    "url": best_pair.get("url", f"https://dexscreener.com/solana/{token_address}"),
                    "socials": {
                        "twitter": best_pair.get("links", {}).get("twitter"),
                        "website": best_pair.get("links", {}).get("website"),
                        "telegram": best_pair.get("links", {}).get("telegram"),
                    },
                    "txns_24h": {
                        "buys": best_pair.get("txns", {}).get("h24", {}).get("buys", 0),
                        "sells": best_pair.get("txns", {}).get("h24", {}).get("sells", 0),
                    },
                }
                return info
        except Exception as e:
            logger.error(f"DexScreener exception for {token_address}: {e}")
            return None

    async def get_sol_price(self) -> float:
        """سعر SOL بالدولار حالياً"""
        # SOL/WETH pair على Raydium كمثال
        url = f"{self.BASE_URL}/pairs/solana/58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
        session = await self.get_session()
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return 0
                data = await resp.json()
                if data and len(data) > 0:
                    return float(data[0].get("priceUsd", 0) or 0)
        except Exception:
            pass
        return 0

    def is_early_entry(self, pair_created_at: Optional[int], hours: int = 24) -> bool:
        """هل العملة جديدة (ضمن X ساعة الماضية)؟"""
        if not pair_created_at:
            return False
        import time
        age_seconds = (int(time.time() * 1000) - pair_created_at) / 1000
        return age_seconds < (hours * 3600)


dexscreener = DexScreenerClient()
