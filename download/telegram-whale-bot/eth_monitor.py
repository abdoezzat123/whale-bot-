"""
مراقب Ethereum
==============
بيراقب محافظ الحيتان على Ethereum - من قنوات الشيلات:
- @ETHTRENDING
- @NeoCallss (أوائل المشترين)
- @mad_apes_gambles

المميزات:
- يستخدم Etherscan API (مجاني 100K request/يوم)
- بيكتشف عمليات شراء meme coins على Uniswap
- إشعار فوري على Telegram

التشغيل:
  python eth_monitor.py
"""
import os
import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import urllib.request

import aiohttp
from dotenv import load_dotenv

from whales import ETH_WHALES

load_dotenv()

# ==================== الإعدادات ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "").strip()
MIN_BUY_USD = float(os.getenv("MIN_BUY_USD", "50"))
MAX_BUY_USD = float(os.getenv("MAX_BUY_USD", "2000000"))
POLL_SECONDS = int(os.getenv("ETH_POLL_SECONDS", "30"))  # Ethereum أبطأ من Solana

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("eth-monitor")

# DEX routers للمتابعة (PancakeSwap, Uniswap)
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
DEX_ROUTERS = {UNISWAP_V2_ROUTER.lower(), UNISWAP_V3_ROUTER.lower()}

# تتبع المعاملات اللي اتبعتت
seen_txs: Set[str] = set()


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


# ==================== Etherscan ====================
async def get_recent_transactions(session: aiohttp.ClientSession, address: str, limit: int = 10) -> List[Dict]:
    """جلب آخر معاملات محفظة على Ethereum"""
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={address}&page=1&offset={limit}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            if data.get("status") == "1":
                return data.get("result", [])
            return []
    except Exception as e:
        log.error(f"Etherscan error: {e}")
        return []


async def get_token_transfers(session: aiohttp.ClientSession, address: str, limit: int = 50) -> List[Dict]:
    """جلب آخر token transfers لمحفظة"""
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=tokentx&address={address}&page=1&offset={limit}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            if data.get("status") == "1":
                return data.get("result", [])
            return []
    except Exception as e:
        log.error(f"Etherscan error: {e}")
        return []


async def get_eth_price(session: aiohttp.ClientSession) -> float:
    """سعر ETH من DexScreener"""
    try:
        url = "https://api.dexscreener.com/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    return float(data[0].get("priceUsd", 0) or 0)
    except Exception:
        pass
    return 0


async def get_token_info_dexscreener(session: aiohttp.ClientSession, token_address: str) -> Optional[Dict]:
    """معلومات العملة من DexScreener"""
    url = f"https://api.dexscreener.com/tokens/v1/ethereum/{token_address}"
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
                "url": best.get("url", f"https://dexscreener.com/ethereum/{token_address}"),
            }
    except Exception as e:
        log.error(f"DexScreener exception: {e}")
        return None


# ==================== تتبع المعاملات ====================
def is_seen(tx_hash: str) -> bool:
    return tx_hash in seen_txs


def mark_seen(tx_hash: str):
    seen_txs.add(tx_hash)
    if len(seen_txs) > 2000:
        # نحتفظ بآخر 2000 معاملة
        seen_txs.clear()
        seen_txs.update(list(seen_txs)[-1000:])


# ==================== تحليل المعاملات ====================
def is_buy_transaction(tx: Dict, whale_address: str) -> Optional[Dict]:
    """
    تحديد لو المعاملة دي عملية شراء token.
    - لو الحوت بعت ETH لـ Uniswap Router = شراء
    """
    try:
        to_address = tx.get("to", "").lower()
        from_address = tx.get("from", "").lower()
        value_wei = int(tx.get("value", "0") or "0")
        value_eth = value_wei / 1e18

        # لو الحوت بعت ETH لـ Uniswap Router = شراء
        if (from_address == whale_address.lower() and
            to_address in DEX_ROUTERS and
            value_eth > 0.001):

            return {
                "whale_address": whale_address,
                "value_eth": value_eth,
                "tx_hash": tx.get("hash", ""),
                "timestamp": int(tx.get("timeStamp", time.time())),
                "to_dex": to_address,
            }
        return None
    except Exception:
        return None


def is_token_buy(token_tx: Dict, whale_address: str) -> Optional[Dict]:
    """
    تحديد لو حصل token transfer للـ whale = شراء token
    """
    try:
        to_addr = token_tx.get("to", "").lower()
        from_addr = token_tx.get("from", "").lower()
        whale_lower = whale_address.lower()

        # لو الـ whale هو الـ to = استلم tokens = شراء
        if to_addr == whale_lower and from_addr not in DEX_ROUTERS:
            value = int(token_tx.get("value", "0")) / (10 ** int(token_tx.get("tokenDecimal", 18)))
            symbol = token_tx.get("tokenSymbol", "?")
            token_addr = token_tx.get("contractAddress", "")

            # نتجاهل الـ stablecoins
            if symbol.upper() in ["USDT", "USDC", "DAI", "WETH"]:
                return None

            if value > 0:
                return {
                    "whale_address": whale_address,
                    "token_address": token_addr,
                    "token_symbol": symbol,
                    "token_amount": value,
                    "tx_hash": token_tx.get("hash", ""),
                    "timestamp": int(token_tx.get("timeStamp", time.time())),
                }
        return None
    except Exception:
        return None


# ==================== الإشعار ====================
async def notify_eth_buy(whale: Dict, buy: Dict, session: aiohttp.ClientSession, eth_price: float, source: str = ""):
    """إرسال إشعار شراء على Ethereum"""
    name = whale.get("name", "Unknown Whale")
    note = whale.get("note", "")

    cairo_tz = timezone(timedelta(hours=3))
    tx_dt = datetime.fromtimestamp(buy["timestamp"], tz=cairo_tz)
    tx_time_str = tx_dt.strftime("%H:%M:%S")
    tx_date_str = tx_dt.strftime("%d/%m/%Y")

    delay_seconds = int(time.time() - buy["timestamp"])
    if delay_seconds < 5:
        delay_str = "⚡ لحظي!"
    elif delay_seconds < 60:
        delay_str = f"⚡ {delay_seconds} ثانية"
    else:
        delay_str = f"{delay_seconds // 60} دقيقة"

    # قيمة الشراء بالدولار
    if "value_eth" in buy:
        value_usd = buy["value_eth"] * eth_price if eth_price else 0
        value_str = f"${value_usd:,.0f} ({buy['value_eth']:.4f} ETH)"
        token_info_str = "غير معروف (لو معاملة DEX مباشرة)"
    else:
        # token buy
        info = await get_token_info_dexscreener(session, buy.get("token_address", ""))
        if info:
            symbol = info.get("symbol", "???")
            token_name = info.get("name", "Unknown")
            price = info.get("price_usd", 0)
            liquidity = info.get("liquidity_usd", 0)
            mcap = info.get("market_cap", 0)
            volume = info.get("volume_24h", 0)
            url = info.get("url", "")
            dex = info.get("dex_id", "?")

            # حساب القيمة بالدولار
            value_usd = buy.get("token_amount", 0) * price

            def format_usd(val):
                if val >= 1e9: return f"${val/1e9:.2f}B"
                elif val >= 1e6: return f"${val/1e6:.2f}M"
                elif val >= 1e3: return f"${val/1e3:.1f}K"
                elif val > 0: return f"${val:.4f}"
                return "؟"

            price_str = f"${price:.8f}" if price < 0.01 else f"${price:.4f}"

            # إشعار خاص للمطورين المعروفين
            is_famous = whale.get("is_famous", False)
            if is_famous:
                header = f"🚨🏆 <b>{name}</b> اشترى على ETH!"
                footer = "\n⚠️ مطور مشهور - ممكن تطير 5x-100x!"
            else:
                header = f"🐋 <b>{name}</b> اشترى على ETH!"
                footer = ""

            tx_link = f"https://etherscan.io/tx/{buy['tx_hash']}"
            ds_link = f"https://dexscreener.com/ethereum/{buy.get('token_address', '?')}"
            
            text = f"""{header} {delay_str}

🪙 <b>{symbol}</b> - {token_name}
<code>{buy.get('token_address', '?')}</code>

💰 {format_usd(value_usd)}
🏷️ {format_usd(mcap)}
⏰ شراء: {tx_time_str}
📡 وصول: {datetime.now(cairo_tz).strftime("%H:%M:%S")}

🔗 <a href="{ds_link}">Chart</a> | <a href="{tx_link}">TX</a>{footer}
"""
            log.info(f"📤 ETH buy alert: {name} bought {symbol} ({format_usd(value_usd)})")
            await send_telegram(text, session)
            return
        else:
            value_str = f"{buy.get('token_amount', 0):,.0f} {buy.get('token_symbol', '?')}"
            token_info_str = f"{buy.get('token_symbol', '?')} - {buy.get('token_address', '?')[:20]}..."
            url = f"https://etherscan.io/token/{buy.get('token_address', '')}"

            text = f"""
🚨 <b>حوت ETH اشترى!</b> {delay_str}

⏰ <b>الوقت:</b> {tx_time_str} ({tx_date_str}) - توقيت القاهرة
👤 <b>الحوت:</b> {name}
{f"📝 {note}" if note else ""}
{f"📡 المصدر: {source}" if source else ""}

🪙 <b>العملة:</b> {token_info_str}
💰 <b>القيمة:</b> {value_str}

🔗 <a href="{url}">Etherscan</a> | <a href="https://etherscan.io/tx/{buy['tx_hash']}">TX</a>
🏦 <a href="https://etherscan.io/address/{whale['address']}">المحفظة</a>
"""
            log.info(f"📤 ETH buy alert: {name} bought {value_str}")
            await send_telegram(text, session)
            return

    # لو شراء بـ ETH مباشرة
    tx_link = f"https://etherscan.io/tx/{buy['tx_hash']}"
    wallet_link = f"https://etherscan.io/address/{whale['address']}"
    
    text = f"""🐋 <b>{name}</b> ETH! {delay_str}

💰 {value_str}
⏰ <b>{tx_time_str}</b> ({tx_date_str})

🔗 <a href="{tx_link}">TX</a> | <a href="{wallet_link}">Wallet</a>
"""
    log.info(f"📤 ETH buy alert: {name} spent {buy['value_eth']:.4f} ETH")
    await send_telegram(text, session)


# ==================== الحلقة الرئيسية ====================
async def poll_eth_whale(whale: Dict, session: aiohttp.ClientSession, eth_price: float):
    """فحص محفظة حوت ETH واحدة"""
    address = whale["address"]
    name = whale.get("name", "Unknown Whale")
    source = whale.get("source", "")
    try:
        # نجيب آخر token transfers (أسرع في كشف الشراء)
        txs = await get_token_transfers(session, address, limit=10)
        if not txs:
            return

        for tx in txs:
            tx_hash = tx.get("hash", "")
            if not tx_hash or is_seen(tx_hash):
                continue

            buy = is_token_buy(tx, address)
            if buy:
                # فلتر: نتخطى المعاملات القديمة (أقدم من 10 دقايق)
                tx_age = int(time.time() - buy.get("timestamp", 0))
                if tx_age > 600:
                    mark_seen(tx_hash)
                    continue

                value_usd = 0  # هنحسبها من token_info
                # فلترة ONLY_FAMOUS
                is_famous = whale.get("is_famous", False)
                only_famous = os.getenv("ONLY_FAMOUS", "false").strip().lower() == "true"
                if only_famous and not is_famous:
                    pass  # نتجاهل الحيتان العاديين
                else:
                    # فلتر MC: نشوف قيمة العملة
                    token_info_check = await get_token_info_dexscreener(session, buy.get("token_address", ""))
                    if token_info_check:
                        token_mcap = token_info_check.get("market_cap", 0)
                        if token_mcap > MAX_BUY_USD:
                            mark_seen(tx_hash)
                            continue
                    await notify_eth_buy(whale, buy, session, eth_price, source)

            mark_seen(tx_hash)

    except Exception as e:
        log.error(f"Error polling ETH whale {name}: {e}")


async def main():
    log.info("🚀 بدء تشغيل مراقب Ethereum")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("❌ إعدادات Telegram ناقصة في .env")
        return
    if not ETHERSCAN_API_KEY:
        log.error("❌ ETHERSCAN_API_KEY ناقصة في .env")
        return

    log.info(f"📋 عدد محافظ ETH المتابعة: {len(ETH_WHALES)}")
    log.info(f"💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}")
    log.info(f"⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية")

    async with aiohttp.ClientSession() as session:
        # رسالة تأكيد التشغيل
        await send_telegram(
            f"🚀 <b>مراقب Ethereum اشتغل!</b>\n\n"
            f"🐋 محافظ ETH متابعة: {len(ETH_WHALES)}\n"
            f"💰 حد الشراء: ${MIN_BUY_USD:,.0f}\n"
            f"⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية\n\n"
            f"📡 المصادر: ETHTRENDING، NeoCallss، mad_apes_gambles",
            session
        )

        last_eth_price_update = 0
        eth_price = 0

        while True:
            try:
                # تحديث سعر ETH كل 60 ثانية
                if time.time() - last_eth_price_update > 60:
                    new_price = await get_eth_price(session)
                    if new_price > 0:
                        eth_price = new_price
                        last_eth_price_update = time.time()
                        log.info(f"💰 سعر ETH: ${eth_price:.2f}")

                # فحص كل المحافظ بالتوازي
                tasks = [poll_eth_whale(w, session, eth_price) for w in ETH_WHALES]
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
