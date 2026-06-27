"""
عميل Helius API
===============
Helius هو أفضل API لـ Solana - بيقدم:
- parsed transaction history
- token balances
- webhooks (لو حابب نستخدم بدل الـ polling)

الـ free tier: 100K request شهرياً، يكفي جداً لرصد ~50 محفظة كل 30 ثانية.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp

from config import config

logger = logging.getLogger(__name__)

# Rate limiter بسيط
class RateLimiter:
    def __init__(self, max_per_second: int = 10):
        self.max_per_second = max_per_second
        self.semaphore = asyncio.Semaphore(max_per_second)

    async def acquire(self):
        async with self.semaphore:
            await asyncio.sleep(1.0 / self.max_per_second)


rate_limiter = RateLimiter(max_per_second=8)  # محافظ para Helius free tier


class HeliusClient:
    def __init__(self):
        self.rpc_url = config.HELIUS_RPC_URL
        self.api_url = config.HELIUS_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def rpc_call(self, method: str, params: list) -> Optional[Dict]:
        """استدعاء RPC method على Helius"""
        await rate_limiter.acquire()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        session = await self.get_session()
        try:
            async with session.post(self.rpc_url, json=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Helius RPC error {resp.status}: {await resp.text()}")
                    return None
                data = await resp.json()
                if "error" in data:
                    logger.error(f"Helius RPC error: {data['error']}")
                    return None
                return data.get("result")
        except Exception as e:
            logger.error(f"Helius RPC exception: {e}")
            return None

    async def get_signatures_for_address(
        self, address: str, limit: int = 10, before: Optional[str] = None
    ) -> List[Dict]:
        """جلب آخر معاملات محفظة"""
        params = [address, {"limit": limit}]
        if before:
            params[1]["before"] = before
        result = await self.rpc_call("getSignaturesForAddress", params)
        if not result:
            return []
        return result

    async def get_parsed_transaction(self, signature: str) -> Optional[Dict]:
        """جلب تفاصيل معاملة كاملة parsed"""
        result = await self.rpc_call(
            "getTransaction",
            [signature, {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}],
        )
        return result

    async def get_token_balances(self, address: str) -> List[Dict]:
        """جلب رصيد tokens لمحفظة"""
        result = await self.rpc_call(
            "getTokenAccountsByOwner",
            [
                address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )
        if not result:
            return []
        return [
            {
                "mint": acc["account"]["data"]["parsed"]["info"]["mint"],
                "amount": acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"],
                "owner": acc["account"]["data"]["parsed"]["info"]["owner"],
            }
            for acc in result.get("value", [])
        ]


helius = HeliusClient()
