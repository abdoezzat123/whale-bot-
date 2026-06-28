"""
مراقب BSC (Binance Smart Chain)
================================
بيراقب محافظ SHIB/FLOKI/CZ على Binance Smart Chain.

المميزات:
- يستخدم BSC public RPCs مجانية (مفيش API key)
- بيكتشف عمليات شراء meme coins على PancakeSwap
- بيتبع نفس ستايل إشعارات Solana

الاستخدام:
- بيشتغل بشكل مستقل عن bot.py
- تشغله في terminal تاني: python bsc_monitor.py
- أو تفعّله في docker-compose.yml

المحافظ المتابعة موجودة في whales.py → BSC_WHALES
"""
import os
import asyncio
import logging
import time
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

import aiohttp
from dotenv import load_dotenv

# استيراد المحافظ من whales.py
from whales import BSC_WHALES, ETH_WHALES

load_dotenv()

# ==================== الإعدادات ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
MIN_BUY_USD = float(os.getenv("MIN_BUY_USD", "500"))
POLL_SECONDS = int(os.getenv("BSC_POLL_SECONDS", "10"))  # BSC أبطأ من Solana

# Multi-RPC BSC public endpoints (مجانية 100%)
BSC_RPCS = [
    "https://bsc-dataseed.binance.org",                    # Binance official
    "https://bsc-dataseed1.defibit.io",                    # Defibit
    "https://bsc-dataseed1.ninicoin.io",                   # Ninicoin
    "https://bsc.publicnode.com",                          # PublicNode
    "https://rpc.ankr.com/bsc",                            # Ankr
]

# إحصائيات RPC
rpc_stats = {rpc: {"success": 0, "fail": 0} for rpc in BSC_RPCS}

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bsc-monitor")

# ==================== عناوين مهمة ====================
# WBNB (Wrapped BNB) - زي WSOL على Solana
WBNB_ADDRESS = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"

# USDT على BSC
USDT_ADDRESS = "0x55d398326f99059ff775485246999027b3197955"

# PancakeSwap Router V2
PANCAKE_ROUTER = "0x10ed43c718714eb63d5aa57b78b54704e256024e"

# PancakeSwap Router V3
PANCAKE_ROUTER_V3 = "0x13f4ea83d0bd40e75c8222255bc855a974568dd4"

# DEX addresses للمتابعة
DEX_ADDRESSES = {PANCAKE_ROUTER, PANCAKE_ROUTER_V3}

# ==================== Multi-RPC ====================
async def bsc_rpc(session: aiohttp.ClientSession, method: str, params: list) -> Optional[Dict]:
    """استدعاء BSC RPC method على عدة endpoints"""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}

    # ترتيب الـ RPCs حسب نسبة النجاح
    def score(rpc):
        s = rpc_stats[rpc]["success"]
        f = rpc_stats[rpc]["fail"]
        return -(s / max(s + f, 1))
    rpcs = sorted(BSC_RPCS, key=score)

    async def try_rpc(rpc_url: str) -> Optional[Dict]:
        try:
            async with session.post(rpc_url, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    rpc_stats[rpc_url]["fail"] += 1
                    return None
                data = await resp.json()
                if "error" in data:
                    rpc_stats[rpc_url]["fail"] += 1
                    return None
                rpc_stats[rpc_url]["success"] += 1
                return data.get("result")
        except Exception:
            rpc_stats[rpc_url]["fail"] += 1
            return None

    # نجرّب أول 3 بالتوازي
    tasks = [try_rpc(rpc) for rpc in rpcs[:3]]
    for result in await asyncio.gather(*tasks):
        if result is not None:
            return result

    # لو فشلوا، نجرّب الباقي
    for rpc in rpcs[3:]:
        result = await try_rpc(rpc)
        if result is not None:
            return result
    return None


async def get_bnb_balance(session: aiohttp.ClientSession, address: str) -> float:
    """رصيد BNB لمحفظة"""
    result = await bsc_rpc(session, "eth_getBalance", [address, "latest"])
    if result:
        try:
            return int(result, 16) / 1e18
        except (ValueError, TypeError):
            pass
    return 0


async def get_token_balance(session: aiohttp.ClientSession, token_address: str, wallet_address: str) -> float:
    """رصيد ERC-20 token لمحفظة باستخدام balanceOf"""
    # balanceOf(address) selector = 0x70a08231
    padded_wallet = wallet_address[2:].lower().zfill(64)
    data = f"0x70a08231{padded_wallet}"

    result = await bsc_rpc(session, "eth_call", [
        {"to": token_address, "data": data},
        "latest"
    ])
    if result and result != "0x":
        try:
            return int(result, 16) / 1e18
        except (ValueError, TypeError):
            pass
    return 0


async def get_recent_transactions(session: aiohttp.ClientSession, address: str, limit: int = 10) -> List[Dict]:
    """
    جلب آخر معاملات محفظة على BSC.
    يستخدم BSCScan API (مجاني بدون مفتاح للحد اليومي 5 req/sec)
    """
    url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&page=1&offset={limit}&sort=desc&apikey=YourApiKeyToken"
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("result", []) if data.get("status") == "1" else []
    except Exception as e:
        log.error(f"BSCScan error: {e}")
        return []


async def get_token_info_dexscreener(session: aiohttp.ClientSession, token_address: str) -> Optional[Dict]:
    """معلومات العملة من DexScreener"""
    url = f"https://api.dexscreener.com/tokens/v1/bsc/{token_address}"
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return None
            pairs = await resp.json()
            if not pairs:
                return None
            best = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
            return {
                "symbol": best.get("baseToken", {}).get("symbol", "???"),
                "name": best.get("baseToken", {}).get("name", "Unknown"),
                "price_usd": float(best.get("priceUsd", 0) or 0),
                "liquidity_usd": float(best.get("liquidity", {}).get("usd", 0) or 0),
                "volume_24h": float(best.get("volume", {}).get("h24", 0) or 0),
                "market_cap": float(best.get("fdv", 0) or 0),
                "dex_id": best.get("dexId", "?"),
                "pair_created_at": best.get("pairCreatedAt"),
                "url": best.get("url", f"https://dexscreener.com/bsc/{token_address}"),
            }
    except Exception as e:
        log.error(f"DexScreener exception: {e}")
        return None


async def get_bnb_price(session: aiohttp.ClientSession) -> float:
    """سعر BNB بالدولار"""
    try:
        url = "https://api.dexscreener.com/pairs/bsc/0x16b9a825e334e0a45f03570b3accf4f1d6f4da03"
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    return float(data[0].get("priceUsd", 0) or 0)
    except Exception:
        pass
    return 0


# ==================== تتبع seen transactions ====================
seen_txs = set()


def is_seen_tx(tx_hash: str) -> bool:
    return tx_hash in seen_txs


def mark_tx_seen(tx_hash: str):
    seen_txs.add(tx_hash)
    # نحتفظ بآخر 1000 معاملة فقط في الذاكرة
    if len(seen_txs) > 1000:
        seen_txs.pop()


# ==================== تحليل المعاملات ====================
def is_buy_transaction(tx: Dict, whale_address: str) -> Optional[Dict]:
    """
    تحديد لو المعاملة دي عملية شراء token.
    منطق مبسط:
    - لو الحوت بعت BNB لـ PancakeSwap router
    - واستلم tokens
    - يبقى ده شراء
    """
    try:
        to_address = tx.get("to", "").lower()
        from_address = tx.get("from", "").lower()
        value_wei = int(tx.get("value", "0") or "0")
        value_bnb = value_wei / 1e18

        # لو الحوت بعت BNB لـ PancakeSwap
        if (from_address == whale_address.lower() and
            to_address in {r.lower() for r in DEX_ADDRESSES} and
            value_bnb > 0.001):  # أكتر من 0.001 BNB

            return {
                "whale_address": whale_address,
                "value_bnb": value_bnb,
                "tx_hash": tx.get("hash", ""),
                "timestamp": int(tx.get("timeStamp", time.time())),
                "to_dex": to_address,
            }
        return None
    except Exception:
        return None


# ==================== Telegram ====================
async def send_telegram(text: str, session: aiohttp.ClientSession):
    if not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            if resp.status != 200:
                log.error(f"Telegram error {resp.status}")
    except Exception as e:
        log.error(f"Telegram exception: {e}")


# ==================== الإشعار ====================
async def notify_bsc_buy(whale: Dict, buy: Dict, session: aiohttp.ClientSession, bnb_price: float):
    """إرسال إشعار شراء على BSC"""
    name = whale.get("name", "Unknown Whale")
    note = whale.get("note", "")

    # الوقت بتوقيت القاهرة
    cairo_tz = timezone(timedelta(hours=3))
    tx_dt = datetime.fromtimestamp(buy["timestamp"], tz=cairo_tz)
    tx_time_str = tx_dt.strftime("%H:%M:%S")
    tx_date_str = tx_dt.strftime("%d/%m/%Y")

    # قيمة الشراء بالدولار
    value_usd = buy["value_bnb"] * bnb_price if bnb_price else 0

    # تنبيه: مش هنعرف الـ token address من المعاملة مباشرة بدون logs
    # فالإشعار هيكون مبسط - نقدر نطورة بـ eth_getTransactionReceipt لو حابب
    delay_seconds = int(time.time() - buy["timestamp"])
    delay_str = "⚡ لحظي!" if delay_seconds < 5 else f"⚡ {delay_seconds} ثانية" if delay_seconds < 60 else f"{delay_seconds // 60} دقيقة"

    text = f"""
🚨 <b>حوت BSC اشترى!</b> {delay_str}

⏰ <b>الوقت:</b> {tx_time_str} ({tx_date_str}) - توقيت القاهرة
👤 <b>الحوت:</b> {name}
{f"📝 {note}" if note else ""}

💰 <b>قيمة الشراء:</b> ${value_usd:,.0f} ({buy['value_bnb']:.4f} BNB)
🔗 <b>DEX:</b> PancakeSwap

🔗 <a href="https://bscscan.com/tx/{buy['tx_hash']}">BSCScan TX</a>
🏦 <a href="https://bscscan.com/address/{whale['address']}">المحفظة</a>

⚠️ <b>ملاحظة:</b> البوت بيراقب BNB outgoing للـ PancakeSwap. للتفاصيل الكاملة شوف الـ tx على BSCScan.
"""
    log.info(f"📤 BSC buy alert: {name} spent {buy['value_bnb']:.4f} BNB (${value_usd:,.0f})")
    await send_telegram(text, session)


# ==================== الحلقة الرئيسية ====================
async def poll_bsc_whale(whale: Dict, session: aiohttp.ClientSession, bnb_price: float):
    """فحص محفظة حوت BSC واحدة"""
    address = whale["address"]
    name = whale.get("name", "Unknown Whale")
    try:
        txs = await get_recent_transactions(session, address, limit=10)
        if not txs:
            return

        for tx in reversed(txs):  # الأقدم الأول
            tx_hash = tx.get("hash", "")
            if not tx_hash or is_seen_tx(tx_hash):
                continue

            buy = is_buy_transaction(tx, address)
            if buy:
                value_usd = buy["value_bnb"] * bnb_price if bnb_price else 0
                if value_usd >= MIN_BUY_USD:
                    await notify_bsc_buy(whale, buy, session, bnb_price)

            mark_tx_seen(tx_hash)
    except Exception as e:
        log.error(f"Error polling BSC whale {name}: {e}")


async def main():
    log.info("🚀 بدء تشغيل مراقب BSC")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("❌ إعدادات Telegram ناقصة في .env")
        return

    log.info(f"📋 عدد محافظ BSC المتابعة: {len(BSC_WHALES)}")
    log.info(f"💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}")
    log.info(f"⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية")

    async with aiohttp.ClientSession() as session:
        # رسالة تأكيد التشغيل
        await send_telegram(
            f"🚀 <b>مراقب BSC اشتغل!</b>\n\n🐋 محافظ BSC متابعة: {len(BSC_WHALES)}\n"
            f"💰 حد الشراء: ${MIN_BUY_USD:,.0f}\n"
            f"⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية\n\n"
            f"بيراقب: SHIB + FLOKI + CZ wallets على Binance Smart Chain",
            session
        )

        last_bnb_price_update = 0
        bnb_price = 0

        while True:
            try:
                # تحديث سعر BNB كل 60 ثانية
                if time.time() - last_bnb_price_update > 60:
                    new_price = await get_bnb_price(session)
                    if new_price > 0:
                        bnb_price = new_price
                        last_bnb_price_update = time.time()
                        log.info(f"💰 سعر BNB: ${bnb_price:.2f}")

                # فحص كل المحافظ بالتوازي
                tasks = [poll_bsc_whale(w, session, bnb_price) for w in BSC_WHALES]
                await asyncio.gather(*tasks, return_exceptions=True)

                await asyncio.sleep(POLL_SECONDS)
            except KeyboardInterrupt:
                log.info("إيقاف المراقب...")
                break
            except Exception as e:
                log.error(f"Main loop error: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
