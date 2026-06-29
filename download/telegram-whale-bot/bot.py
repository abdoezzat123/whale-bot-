"""
بوت تتبع حيتان Meme Coins على Solana
====================================
- بيراقب محافظ الحيتان على شبكة Solana
- بيبعت إشعار فوري على Telegram لما أي حوت يشتري meme coin
- بيجيب بيانات العملة من DexScreener (مجاني)
- يستخدم Multi-RPC مجاني بدون أي API key

التشغيل:
  1. python3 -m venv venv && source venv/bin/activate
  2. pip install -r requirements.txt
  3. املأ .env بالقيم (TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID)
  4. python bot.py
"""
import os
import asyncio
import logging
import sqlite3
import time
import json
import random
from typing import Dict, List, Optional, Set
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# ==================== الإعدادات ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
MIN_BUY_USD = float(os.getenv("MIN_BUY_USD", "500"))
MAX_BUY_USD = float(os.getenv("MAX_BUY_USD", "2000000"))  # فوق 2M نتجاهل
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))  # 5 ثواني = شبه real-time
ONLY_FAMOUS = os.getenv("ONLY_FAMOUS", "false").strip().lower() == "true"  # فلترة الإشعارات

# ==================== Multi-RPC Endpoints مجانية 100% ====================
# لو عندك Helius API key، حطها في .env وهيُستخدم تلقائياً (أقوى وأسرع)
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()

# قائمة RPC endpoints مجانية بترتيب الأولوية
# Helius لو موجود، بعدها باقي الـ public RPCs
PUBLIC_RPCS = [
    "https://api.mainnet-beta.solana.com",                # Solana official (40 req/sec)
    "https://solana-mainnet.rpc.extrnode.com",            # Triton public
    "https://rpc.ankr.com/solana",                        # Ankr public
    "https://solana-mainnet.g.alchemy.com/v2/demo",       # Alchemy demo
    "https://mainnet.solana-rpc.com",                     # Public
]

# لو عندك Helius، نحطه الأول
ALL_RPCS = []
if HELIUS_API_KEY:
    ALL_RPCS.append(f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}")
ALL_RPCS.extend(PUBLIC_RPCS)

# إحصائيات الـ RPCs (للتتبع أي endpoint أفضل)
rpc_stats: Dict[str, Dict] = {rpc: {"success": 0, "fail": 0} for rpc in ALL_RPCS}

# قاعدة بيانات SQLite بسيطة (file واحد)
DB_PATH = Path(__file__).parent / "seen.db"

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("whale-bot")

# ==================== إعدادات التجميع ====================
# 3 حيتان يشتروا نفس العملة في 6 ساعات = إشعار "🔥 تجميع"
ACCUMULATION_THRESHOLD = int(os.getenv("ACCUMULATION_THRESHOLD", "3"))
ACCUMULATION_WINDOW_HOURS = int(os.getenv("ACCUMULATION_WINDOW_HOURS", "6"))
# منع تكرار إشعارات التجميع لنفس العملة (ساعة بين كل إشعار)
ACCUMULATION_COOLDOWN_HOURS = int(os.getenv("ACCUMULATION_COOLDOWN_HOURS", "3"))

# ==================== قاعدة البيانات ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_txs (
            signature TEXT PRIMARY KEY,
            seen_at INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_whales (
            address TEXT PRIMARY KEY,
            name TEXT,
            added_at INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS whale_buys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            whale_address TEXT NOT NULL,
            whale_name TEXT,
            token_address TEXT NOT NULL,
            token_symbol TEXT,
            amount_usd REAL,
            amount_sol REAL,
            timestamp INTEGER NOT NULL,
            signature TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_buys_token
            ON whale_buys(token_address, timestamp)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accumulation_alerts (
            token_address TEXT PRIMARY KEY,
            last_alert_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

def is_seen(signature: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM seen_txs WHERE signature = ?", (signature,)).fetchone()
    conn.close()
    return row is not None

def mark_seen(signature: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO seen_txs (signature, seen_at) VALUES (?, ?)",
                 (signature, int(time.time())))
    conn.commit()
    conn.close()

def add_user_whale(address: str, name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO user_whales (address, name, added_at) VALUES (?, ?, ?)",
                 (address, name, int(time.time())))
    conn.commit()
    conn.close()

def remove_user_whale(address: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("DELETE FROM user_whales WHERE address = ?", (address,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok

def list_user_whales() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT address, name FROM user_whales").fetchall()
    conn.close()
    return [{"address": r[0], "name": r[1]} for r in rows]


# ==================== دوال التجميع ====================
def log_whale_buy(whale_address: str, whale_name: str, token_address: str,
                  token_symbol: str, amount_usd: float, amount_sol: float,
                  signature: str, timestamp: int):
    """تسجيل عملية شراء حوت في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO whale_buys
           (whale_address, whale_name, token_address, token_symbol,
            amount_usd, amount_sol, timestamp, signature)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (whale_address, whale_name, token_address, token_symbol,
         amount_usd, amount_sol, timestamp, signature)
    )
    conn.commit()
    conn.close()


def get_recent_buys_for_token(token_address: str, hours: int) -> List[Dict]:
    """كل عمليات شراء الحيتان على عملة معينة في آخر X ساعة"""
    cutoff = int(time.time()) - (hours * 3600)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """SELECT whale_address, whale_name, token_symbol, amount_usd,
                  amount_sol, timestamp, signature
           FROM whale_buys
           WHERE token_address = ? AND timestamp >= ?
           ORDER BY timestamp ASC""",
        (token_address, cutoff)
    ).fetchall()
    conn.close()
    return [{"whale_address": r[0], "whale_name": r[1], "token_symbol": r[2],
             "amount_usd": r[3], "amount_sol": r[4], "timestamp": r[5],
             "signature": r[6]} for r in rows]


def get_unique_whales_count_for_token(token_address: str, hours: int) -> int:
    """عدد الحيتان الفريدين اللي اشتروا العملة في آخر X ساعة"""
    cutoff = int(time.time()) - (hours * 3600)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        """SELECT COUNT(DISTINCT whale_address) as cnt
           FROM whale_buys
           WHERE token_address = ? AND timestamp >= ?""",
        (token_address, cutoff)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def can_send_accumulation_alert(token_address: str) -> bool:
    """هل ممكن نبعت إشعار تجميع؟ (مش ضمن cooldown)"""
    cutoff = int(time.time()) - (ACCUMULATION_COOLDOWN_HOURS * 3600)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT last_alert_at FROM accumulation_alerts WHERE token_address = ?",
        (token_address,)
    ).fetchone()
    conn.close()
    if not row:
        return True
    return row[0] < cutoff


def mark_accumulation_alert_sent(token_address: str):
    """تعليم إن إشعار التجميع اتبعت"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO accumulation_alerts
           (token_address, last_alert_at) VALUES (?, ?)""",
        (token_address, int(time.time()))
    )
    conn.commit()
    conn.close()

# ==================== قائمة المحافظ ====================
def get_all_whales() -> List[Dict]:
    """دمج محافظ whales.py + المحافظ اللي ضافها المستخدم"""
    from whales import WHALES as DEFAULT_WHALES
    all_w = list(DEFAULT_WHALES)
    for uw in list_user_whales():
        all_w.append({"name": uw["name"], "address": uw["address"], "note": "مضافة من المستخدم"})
    # إزالة التكرار بناءً على الـ address
    seen_addr = set()
    unique = []
    for w in all_w:
        if w["address"] not in seen_addr:
            unique.append(w)
            seen_addr.add(w["address"])
    return unique

# ==================== Telegram ====================
async def send_telegram(text: str, session: aiohttp.ClientSession):
    if not TELEGRAM_CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID غير مضبوط في .env - الإشعار مش هيتبعت")
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
                log.error(f"Telegram error {resp.status}: {await resp.text()}")
    except Exception as e:
        log.error(f"Telegram exception: {e}")

# ==================== Multi-RPC System ====================
def get_sorted_rpcs() -> List[str]:
    """ترتيب الـ RPCs حسب نسبة النجاح (الأفضل أولاً)"""
    def score(rpc):
        s = rpc_stats[rpc]["success"]
        f = rpc_stats[rpc]["fail"]
        return -(s / max(s + f, 1))  # أعلى نسبة نجاح الأول
    return sorted(ALL_RPCS, key=score)

async def rpc_call(session: aiohttp.ClientSession, method: str, params: list) -> Optional[Dict]:
    """
    استدعاء RPC method على عدة endpoints بالتوازي.
    بترجع أول نتيجة ناجحة.
    """
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    rpcs = get_sorted_rpcs()

    # نجرّب أول 3 RPCs بالتوازي
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
    for result in await asyncio.gather(*tasks, return_exceptions=False):
        if result is not None:
            return result

    # لو كلهم فشلوا، نجرّب الباقي بالتتابع
    for rpc in rpcs[3:]:
        result = await try_rpc(rpc)
        if result is not None:
            return result
    return None

async def get_recent_signatures(session: aiohttp.ClientSession, address: str, limit: int = 8) -> List[Dict]:
    result = await rpc_call(session, "getSignaturesForAddress", [address, {"limit": limit}])
    return result if result else []

async def get_parsed_tx(session: aiohttp.ClientSession, signature: str) -> Optional[Dict]:
    result = await rpc_call(session, "getTransaction",
                            [signature, {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
    return result

# ==================== DexScreener ====================
async def get_token_info(session: aiohttp.ClientSession, token_address: str) -> Optional[Dict]:
    url = f"https://api.dexscreener.com/tokens/v1/solana/{token_address}"
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return None
            pairs = await resp.json()
            if not pairs:
                return None
            # اختيار أعلى pair سيولة
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
                "url": best.get("url", f"https://dexscreener.com/solana/{token_address}"),
                "socials": best.get("links", {}),
            }
    except Exception as e:
        log.error(f"DexScreener exception: {e}")
        return None

# ==================== كشف عمليات الشراء ====================
# DEX programs على Solana - اللي بنشوف منها عمليات الـ swap
DEX_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium V4 AMM
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",   # Jupiter v4
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",   # Jupiter v6
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca Whirlpools
    "M2mx93tUckJzCz7VgUi8VRd5wQzk5RxUWmRdD1VwTu6",  # Metaplex Token
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",  # Pump.fun AMM
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",  # Pump.fun
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",  # Pump.fun program
}

# SPL Token program - لتحويلات الـ tokens
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

# Wrapped SOL mint
WSOL_MINT = "So11111111111111111111111111111111111111112"

def analyze_buy_tx(tx_data: Dict, whale_address: str) -> Optional[Dict]:
    """
    تحليل معاملة وتحديد لو فيها عملية شراء meme coin.

    المنطق المطوّر (أكتر شمولية):
    - أي token جديد دخل للمحفظة (بعد أي نوع من الدفع: SOL, USDC, أو swap)
    - يبقى ده "شراء"

    بيرجع:
    {
        "token_mint": str,
        "token_amount": float,
        "sol_amount": float,  # تقديري من تغير الـ SOL
        "value_usd": float,
        "signature": str,
        "timestamp": int,
    }
    أو None لو مش عملية شراء
    """
    if not tx_data:
        return None

    try:
        msg = tx_data.get("meta")
        if not msg or msg.get("err"):
            return None

        pre_token_balances = msg.get("preTokenBalances", []) or []
        post_token_balances = msg.get("postTokenBalances", []) or []

        # نحسب التغير في رصيد المحفظة لكل token
        balance_changes = {}  # mint -> {before, after}
        for pb in pre_token_balances:
            if pb.get("owner") == whale_address:
                mint = pb.get("mint")
                balance_changes.setdefault(mint, {"before": 0, "after": 0})
                balance_changes[mint]["before"] = pb.get("uiTokenAmount", {}).get("uiAmount", 0) or 0

        for pb in post_token_balances:
            if pb.get("owner") == whale_address:
                mint = pb.get("mint")
                balance_changes.setdefault(mint, {"before": 0, "after": 0})
                balance_changes[mint]["after"] = pb.get("uiTokenAmount", {}).get("uiAmount", 0) or 0

        # لو فيه SOL خرج + token دخل = شراء
        sol_change = balance_changes.get(WSOL_MINT, {"before": 0, "after": 0})
        sol_diff = (sol_change["after"] or 0) - (sol_change["before"] or 0)

        bought_tokens = []
        for mint, change in balance_changes.items():
            if mint == WSOL_MINT:
                continue
            # نتجاهل الـ stablecoins المعروفة (USDC, USDT)
            if mint in ["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                         "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"]:  # USDT
                continue
            diff = (change["after"] or 0) - (change["before"] or 0)
            if diff > 0:  # زاد الرصيد = استلم tokens
                bought_tokens.append({
                    "mint": mint,
                    "amount": diff,
                })

        # كمان نشوف native SOL لو الحوت دفع
        fee_payer_balance_change = 0
        try:
            pre_balances = msg.get("preBalances", []) or []
            post_balances = msg.get("postBalances", []) or []
            account_keys = tx_data.get("transaction", {}).get("message", {}).get("accountKeys", []) or []
            for i, key in enumerate(account_keys):
                key_str = key.get("pubkey") if isinstance(key, dict) else key
                if key_str == whale_address and i < len(pre_balances) and i < len(post_balances):
                    fee_payer_balance_change = (post_balances[i] - pre_balances[i]) / 1e9
                    break
        except Exception:
            pass

        total_sol_out = -sol_diff + max(0, -fee_payer_balance_change)

        # ✅ المنطق الجديد المُطوّر:
        # لو فيه tokens اتشترت (دخلت للمحفظة) - نبعت إشعار بغض النظر عن طريقة الدفع
        if not bought_tokens:
            return None

        # نختار أكبر token تم شراؤه
        biggest = max(bought_tokens, key=lambda t: t["amount"])
        sol_paid = total_sol_out if total_sol_out > 0 else 0

        return {
            "token_mint": biggest["mint"],
            "token_amount": biggest["amount"],
            "sol_amount": sol_paid,
            "signature": tx_data.get("transaction", {}).get("signatures", [""])[0],
            "timestamp": tx_data.get("blockTime") or int(time.time()),
            "slot": tx_data.get("slot"),
        }
    except Exception as e:
        log.error(f"Error analyzing tx: {e}")
        return None

# ==================== الحلقة الرئيسية ====================
async def poll_whale(whale: Dict, session: aiohttp.ClientSession, sol_price: float):
    """فحص محفظة حوت واحدة"""
    address = whale["address"]
    name = whale.get("name", "Unknown Whale")
    try:
        sigs = await get_recent_signatures(session, address, limit=6)
        if not sigs:
            return

        # نعكس الترتيب علشان نعالج الأقدم الأول (لو فيه أكثر من واحد جديد)
        for sig_info in reversed(sigs):
            sig = sig_info.get("signature", "")
            if not sig or sig_info.get("err"):
                continue
            if is_seen(sig):
                continue

            # نجيب تفاصيل المعاملة
            tx = await get_parsed_tx(session, sig)
            buy = analyze_buy_tx(tx, address)

            if buy:
                # نحسب القيمة بالدولار
                value_usd = buy["sol_amount"] * sol_price if sol_price else 0
                buy["value_usd"] = value_usd

                # فلتر: نتخطى المعاملات القديمة (أقدم من 10 دقايق)
                tx_age = int(time.time() - buy.get("timestamp", 0))
                if tx_age > 600:
                    mark_seen(sig)
                    continue

                # فلتر حسب الحد الأدنى + ONLY_FAMOUS
                is_famous = whale.get("is_famous", False)
                if value_usd >= MIN_BUY_USD and value_usd <= MAX_BUY_USD:
                    # لو ONLY_FAMOUS=true، نبعت بس للمطورين المعروفين
                    if ONLY_FAMOUS and not is_famous:
                        pass  # نتجاهل الحيتان العاديين
                    else:
                        # نرسل إشعار الشراء العادي
                        await notify_buy(whale, buy, session, sol_price)

                    # نسجل العملية في قاعدة البيانات (علشان التجميع)
                    # نجيب الـ symbol من DexScreener بسرعة
                    info = await get_token_info(session, buy["token_mint"])
                    symbol = info.get("symbol", "???") if info else "???"
                    log_whale_buy(
                        whale_address=address,
                        whale_name=name,
                        token_address=buy["token_mint"],
                        token_symbol=symbol,
                        amount_usd=value_usd,
                        amount_sol=buy["sol_amount"],
                        signature=sig,
                        timestamp=buy.get("timestamp", int(time.time()))
                    )

                    # نفحص التجميع
                    await check_and_notify_accumulation(buy["token_mint"], symbol, info, session)

            # نعلمها كـ seen (سواء شراء أو لأ، علشان ما نفحصهاش تاني)
            mark_seen(sig)

    except Exception as e:
        log.error(f"Error polling {name}: {e}")


async def check_and_notify_accumulation(token_address: str, token_symbol: str,
                                         token_info: Optional[Dict],
                                         session: aiohttp.ClientSession):
    """
    فحص لو فيه تجميع على العملة دي.
    لو 3+ حيتان اشتروا نفس العملة في آخر 6 ساعات = إشعار تجميع.
    """
    unique_whales = get_unique_whales_count_for_token(
        token_address, ACCUMULATION_WINDOW_HOURS
    )

    if unique_whales < ACCUMULATION_THRESHOLD:
        return  # لسه مفيش تجميع

    # لو ضمن cooldown، ما نبعتش
    if not can_send_accumulation_alert(token_address):
        return

    # نجيب كل عمليات الشراء في الفترة
    buys = get_recent_buys_for_token(token_address, ACCUMULATION_WINDOW_HOURS)
    if not buys:
        return

    # نحسب الإجماليات
    total_usd = sum(b["amount_usd"] for b in buys if b["amount_usd"])
    total_sol = sum(b["amount_sol"] for b in buys if b["amount_sol"])

    # نجهز قائمة الحيتان
    whales_list = ""
    seen_whales = set()
    for b in buys:
        if b["whale_address"] not in seen_whales:
            seen_whales.add(b["whale_address"])
            whales_list += f"  • {b['whale_name']} (${b['amount_usd']:,.0f})\n"

    # نحسب الوقت
    first_buy_ts = buys[0]["timestamp"]
    last_buy_ts = buys[-1]["timestamp"]
    duration_min = (last_buy_ts - first_buy_ts) / 60

    from datetime import datetime, timezone, timedelta
    cairo_tz = timezone(timedelta(hours=3))

    # نجهز معلومات العملة
    if token_info:
        price = token_info.get("price_usd", 0)
        liquidity = token_info.get("liquidity_usd", 0)
        mcap = token_info.get("market_cap", 0)
        volume = token_info.get("volume_24h", 0)
        url = token_info.get("url", "")
        dex = token_info.get("dex_id", "?")
        created = token_info.get("pair_created_at")
        age_str = ""
        if created:
            age_h = (int(time.time() * 1000) - created) / 3600000
            if age_h < 1: age_str = f" 🆕 ({int(age_h * 60)} دقيقة)"
            elif age_h < 24: age_str = f" 🆕 ({age_h:.1f} ساعة)"
            else: age_str = f" ({age_h / 24:.1f} يوم)"
    else:
        price = 0
        liquidity = 0
        mcap = 0
        volume = 0
        url = f"https://solscan.io/token/{token_address}"
        dex = "?"
        age_str = ""

    def format_usd(val):
        if val >= 1e9: return f"${val/1e9:.2f}B"
        elif val >= 1e6: return f"${val/1e6:.2f}M"
        elif val >= 1e3: return f"${val/1e3:.1f}K"
        elif val > 0: return f"${val:.4f}"
        return "؟"

    price_str = f"${price:.8f}" if price < 0.01 else f"${price:.4f}"

    text = f"""
🔥 <b>تجميع حيتان!</b> ⚡

⏰ <b>الوقت:</b> {datetime.now(cairo_tz).strftime('%H:%M:%S')} ({datetime.now(cairo_tz).strftime('%d/%m/%Y')})

🪙 <b>العملة:</b> {token_symbol}{age_str}
🐋 <b>عدد الحيتان:</b> {unique_whales} حيتان في {duration_min:.0f} دقيقة
💰 <b>إجمالي الشراء:</b> {format_usd(total_usd)} ({total_sol:.2f} SOL)

<b>الحيتان اللي اشتروا:</b>
{whales_list}
📊 <b>السعر الحالي:</b> {price_str}
💧 <b>السيولة:</b> {format_usd(liquidity)}
📈 <b>الحجم 24h:</b> {format_usd(volume)}
🏷️ <b>Market Cap:</b> {format_usd(mcap)}
🔗 <b>DEX:</b> {dex}

🔗 <a href="{url}">DexScreener</a>
⚠️ <b>تنبيه:</b> ده إشارة قوية إن العملة دي بتجذب حيتان كتير - تابعها بجدية!
"""
    log.info(f"🔥 Accumulation alert: {token_symbol} - {unique_whales} whales in {duration_min:.0f}min")
    await send_telegram(text, session)
    mark_accumulation_alert_sent(token_address)


async def check_token_safety(session, token_mint, token_info):
    """فحص العملة - فرصة ولا خطر؟"""
    safety = {"score": 0, "warnings": [], "opportunity": False}
    
    if not token_info:
        safety["warnings"].append("⚠️ مفيش بيانات")
        return safety
    
    # 1. عمر العملة
    created = token_info.get("pair_created_at")
    if created:
        age_h = (int(time.time() * 1000) - created) / 3600000
        if age_h < 1:
            safety["warnings"].append("🆕 جديدة جداً (أقل من ساعة) - فرصة!")
            safety["opportunity"] = True
        elif age_h < 24:
            safety["warnings"].append("🆕 جديدة (أقل من يوم) - فرصة!")
            safety["opportunity"] = True
        elif age_h < 168:
            safety["warnings"].append("📅 عمرها أقل من أسبوع")
        else:
            safety["warnings"].append("📅 عملة قديمة")
    
    # 2. السيولة
    liquidity = token_info.get("liquidity_usd", 0)
    if liquidity < 5000:
        safety["warnings"].append("🚨 سيولة ضعيفة جداً (< $5K) - خطر rug pull!")
        safety["score"] += 2
    elif liquidity < 20000:
        safety["warnings"].append("💧 سيولة صغيرة (< $20K) - فرصة للنمو")
        safety["opportunity"] = True
    elif liquidity < 100000:
        safety["warnings"].append("💧 سيولة متوسطة - كويسة")
    else:
        safety["warnings"].append("💧 سيولة عالية - آمنة بس مش هتطير 100x")
    
    # 3. Market Cap - ده أهم فحص
    mcap = token_info.get("market_cap", 0)
    if mcap < 100000:
        safety["warnings"].append("💎 MC تحت $100K - فرصة 100x!")
        safety["opportunity"] = True
    elif mcap < 500000:
        safety["warnings"].append("💎 MC تحت $500K - فرصة 10x-50x!")
        safety["opportunity"] = True
    elif mcap < 1000000:
        safety["warnings"].append("📊 MC تحت $1M - فرصة 5x-10x")
    elif mcap < 5000000:
        safety["warnings"].append("📊 MC $1M-$5M - فرصة 2x-5x")
    else:
        safety["warnings"].append("📊 MC عالي ($5M+) - مش هتطير كتير")
    
    # 4. حجم التداول vs السيولة
    volume = token_info.get("volume_24h", 0)
    if volume > 0 and liquidity > 0:
        vol_liq_ratio = volume / liquidity
        if vol_liq_ratio > 10:
            safety["warnings"].append("🔥 حجم تداول ضخم (مضاربة قوية)")
            safety["opportunity"] = True
    
    # التحليل النهائي
    if safety["score"] >= 2:
        safety["warnings"].append("🚨 تحذير: العملة دي فيها مخاطر!")
    elif safety["opportunity"]:
        safety["warnings"].append("✅ فرصة ذهبية - MC صغير وعمر جديد!")
    
    return safety


async def notify_buy(whale: Dict, buy: Dict, session: aiohttp.ClientSession, sol_price: float):
    """إرسال إشعار شراء على Telegram - real-time مع الوقت + Market Cap"""
    name = whale.get("name", "Unknown Whale")
    note = whale.get("note", "")
    token_mint = buy["token_mint"]

    # الوقت الحالي بدقة الثانية
    now = time.time()
    tx_time = buy.get("timestamp", now)
    delay_seconds = int(now - tx_time)

    # صياغة الوقت
    from datetime import datetime, timezone, timedelta
    cairo_tz = timezone(timedelta(hours=3))  # توقيت القاهرة
    tx_dt = datetime.fromtimestamp(tx_time, tz=cairo_tz)
    tx_time_str = tx_dt.strftime("%H:%M:%S")
    tx_date_str = tx_dt.strftime("%d/%m/%Y")

    # delay string
    if delay_seconds < 5:
        delay_str = "⚡ لحظي!"
    elif delay_seconds < 60:
        delay_str = f"⚡ {delay_seconds} ثانية"
    else:
        delay_str = f"{delay_seconds // 60} دقيقة"

    # نحاول نجيب معلومات العملة من DexScreener
    info = await get_token_info(session, token_mint)

    if info:
        symbol = info.get("symbol", "???")
        token_name = info.get("name", "Unknown")
        price = info.get("price_usd", 0)
        liquidity = info.get("liquidity_usd", 0)
        volume = info.get("volume_24h", 0)
        mcap = info.get("market_cap", 0)
        dex = info.get("dex_id", "?")
        url = info.get("url", "")
        created = info.get("pair_created_at")

        # هل العملة جديدة؟
        age_str = ""
        if created:
            age_h = (int(time.time() * 1000) - created) / 3600000
            if age_h < 1:
                age_str = f" 🆕 جديده! ({int(age_h * 60)} دقيقة)"
            elif age_h < 24:
                age_str = f" 🆕 جديده! ({age_h:.1f} ساعة)"
            else:
                age_str = f" ({age_h / 24:.1f} يوم)"
    else:
        symbol = "???"
        token_name = "Unknown"
        price = 0
        liquidity = 0
        volume = 0
        mcap = 0
        dex = "?"
        url = f"https://solscan.io/token/{token_mint}"
        age_str = ""

    # صياغة Market Cap بشكل مختصر
    def format_usd(val):
        if val >= 1_000_000_000:
            return f"${val/1e9:.2f}B"
        elif val >= 1_000_000:
            return f"${val/1e6:.2f}M"
        elif val >= 1_000:
            return f"${val/1e3:.1f}K"
        elif val > 0:
            return f"${val:.2f}"
        return "؟"

    # صياغة الرسالة - أبسط وأوضح
    usd_str = f"${buy['value_usd']:,.0f}" if buy.get("value_usd") else "؟"
    sol_str = f"{buy['sol_amount']:.2f} SOL"
    price_str = f"${price:.10f}" if price < 0.001 else (f"${price:.6f}" if price < 0.01 else f"${price:.4f}")

    # فحص أمان العملة
    safety = await check_token_safety(session, token_mint, info)
    safety_text = ""
    if safety["warnings"]:
        safety_text = "\n\n🔍 <b>تحليل:</b>"
        for w in safety["warnings"]:
            safety_text += f"\n{w}"

    # إشعار خاص للمطورين المعروفين
    is_famous = whale.get("is_famous", False)
    if is_famous:
        header = f"🚨🏆 <b>{name}</b> اشترى!"
        footer = "\n⚠️ مطور مشهور - ممكن تطير 5x-100x!"
    else:
        header = f"🐋 <b>{name}</b> اشترى!"
        footer = ""

    tx_link = f"https://solscan.io/tx/{buy['signature']}"
    wallet_link = f"https://solscan.io/account/{whale['address']}"
    
    text = f"""{header} {delay_str}

🪙 <b>{symbol}</b> - {token_name}{age_str}
<code>{token_mint}</code>

💰 {usd_str} ({sol_str})
🏷️ {format_usd(mcap)} | 💧 {format_usd(liquidity)}
📊 {price_str} | 📈 {format_usd(volume)}

⏰ <b>{tx_time_str}</b> ({tx_date_str})

🔗 <a href="{url}">Chart</a> | <a href="{tx_link}">TX</a> | <a href="{wallet_link}">Wallet</a>{footer}{safety_text}
"""
    log.info(f"📤 Buy alert [{delay_str}]: {name} bought {symbol} ({usd_str}) | MC: {format_usd(mcap)}")
    await send_telegram(text, session)

async def get_sol_price(session: aiohttp.ClientSession) -> float:
    """سعر SOL من DexScreener"""
    try:
        # SOL/USDC pair على Raydium
        url = "https://api.dexscreener.com/pairs/solana/58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    return float(data[0].get("priceUsd", 0) or 0)
    except Exception as e:
        log.error(f"Error getting SOL price: {e}")
    return 0

# ==================== Bot Commands (للإدارة من التيليجرام) ====================
async def handle_telegram_updates(session: aiohttp.ClientSession):
    """استقبال أوامر من التيليجرام (لإضافة/حذف محافظ)"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 25}
            async with session.get(url, params=params, timeout=30) as resp:
                if resp.status != 200:
                    await asyncio.sleep(5)
                    continue
                data = await resp.json()
                if not data.get("ok"):
                    await asyncio.sleep(5)
                    continue
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    if chat_id != TELEGRAM_CHAT_ID:
                        continue  # تجاهل رسائل من الناس التانيين
                    await handle_command(text, session)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            log.error(f"TG updates error: {e}")
            await asyncio.sleep(5)

async def handle_command(text: str, session: aiohttp.ClientSession):
    """معالجة أوامر المستخدم"""
    parts = text.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()
    reply = ""

    if cmd == "/start" or cmd == "/help":
        reply = f"""🐋 <b>بوت تتبع حيتان Meme Coins</b>

<b>الأوامر:</b>
📋 /list - عرض كل المحافظ المتابعة
➕ /add &lt;address&gt; &lt;name&gt; - إضافة محفظة
➖ /remove &lt;address&gt; - حذف محفظة
📊 /stats - إحصائيات سريعة
🔍 /check &lt;address&gt; - بيانات أي عملة فوراً
🔔 /test - إشعار تجريبي للتأكد إن البوت شغال

<b>الإعدادات الحالية:</b>
💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}
⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية
🐋 المحافظ المتابعة: {len(get_all_whales())}

البوت بيراقب المحافظ وبيبعتلك إشعار فوري على موبايلك لما أي حوت يشتري meme coin.
كل إشعار فيه: اسم الحوت، العملة، قيمة الشراء، السعر، السيولة، الحجم، Market Cap، والوقت بتوقيت القاهرة.
"""
    elif cmd == "/list":
        whales = get_all_whales()
        if not whales:
            reply = "مفيش محافظ في القائمة."
        else:
            reply = f"📋 <b>المحافظ المتابعة ({len(whales)}):</b>\n\n"
            for i, w in enumerate(whales, 1):
                reply += f"{i}. <b>{w.get('name', 'بدون اسم')}</b>\n   <code>{w['address']}</code>\n"
                if w.get('note'):
                    reply += f"   📝 {w['note']}\n"
    elif cmd == "/add":
        if len(parts) < 3:
            reply = "الاستخدام: /add <address> <name>\nمثال: /add 5CQw...HFMJ WhaleAlpha"
        else:
            address = parts[1]
            name = " ".join(parts[2:])
            add_user_whale(address, name)
            reply = f"✅ اتضافت المحفظة:\n<b>{name}</b>\n<code>{address}</code>\n\nالبوت هيبدأ يراقبها من دورة الفحص الجاية."
    elif cmd == "/remove":
        if len(parts) < 2:
            reply = "الاستخدام: /remove <address>"
        else:
            address = parts[1]
            if remove_user_whale(address):
                reply = f"✅ اتمسحت المحفظة:\n<code>{address}</code>"
            else:
                reply = f"❌ المحفظة دي مش موجودة في قائمتك (ممكن تكون من whales.py - امسحها يدوياً)"
    elif cmd == "/stats":
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM seen_txs").fetchone()[0]
        whales_count = len(get_all_whales())
        # نحسب إحصائيات RPC
        total_success = sum(s["success"] for s in rpc_stats.values())
        total_fail = sum(s["fail"] for s in rpc_stats.values())
        conn.close()
        reply = f"""📊 <b>إحصائيات البوت</b>

🐋 محافظ متابعة: {whales_count}
📝 معاملات مرصودة: {count}
💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}
⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية

<b>إحصائيات RPC:</b>
✅ نجح: {total_success}
❌ فشل: {total_fail}
📊 نسبة النجاح: {(total_success / max(total_success + total_fail, 1)) * 100:.1f}%
"""
    elif cmd == "/check":
        if len(parts) < 2:
            reply = "الاستخدام: /check <token_address>\nمثال: /check Tqj8yFmagrg7oorpQkVGYR52r96RFTamvWfth9bpump"
        else:
            token_address = parts[1]
            reply = "🔍 بجيب بيانات العملة..."
            await send_telegram(reply, session)
            info = await get_token_info(session, token_address)
            if info:
                def format_usd(val):
                    if val >= 1e9: return f"${val/1e9:.2f}B"
                    elif val >= 1e6: return f"${val/1e6:.2f}M"
                    elif val >= 1e3: return f"${val/1e3:.1f}K"
                    elif val > 0: return f"${val:.4f}"
                    return "؟"
                price = info.get("price_usd", 0)
                price_str = f"${price:.8f}" if price < 0.01 else f"${price:.4f}"
                created = info.get("pair_created_at")
                age_str = ""
                if created:
                    age_h = (int(time.time() * 1000) - created) / 3600000
                    if age_h < 1: age_str = f" ({int(age_h * 60)} دقيقة)"
                    elif age_h < 24: age_str = f" ({age_h:.1f} ساعة)"
                    else: age_str = f" ({age_h / 24:.1f} يوم)"
                reply = f"""🔍 <b>بيانات العملة</b>

🪙 <b>الرمز:</b> {info['symbol']}
📌 <b>الاسم:</b> {info['name']}{age_str}
📊 <b>السعر:</b> {price_str}
💧 <b>السيولة:</b> {format_usd(info['liquidity_usd'])}
📈 <b>الحجم 24h:</b> {format_usd(info['volume_24h'])}
🏷️ <b>Market Cap:</b> {format_usd(info['market_cap'])}
🔗 <b>DEX:</b> {info['dex_id']}

🔗 <a href="{info['url']}">DexScreener</a>
"""
            else:
                reply = "❌ مقدرتش ألاقي العملة دي. تأكد من العنوان."
    elif cmd == "/test":
        # إشعار تجريبي للتأكد إن البوت شغال
        from datetime import datetime, timezone, timedelta
        cairo_tz = timezone(timedelta(hours=3))
        now = datetime.now(cairo_tz)
        test_buy = {
            "token_mint": "Tqj8yFmagrg7oorpQkVGYR52r96RFTamvWfth9bpump",
            "token_amount": 1000000,
            "sol_amount": 68.4,
            "value_usd": 12500,
            "signature": "test_signature_" + str(int(time.time())),
            "timestamp": int(time.time()),
        }
        test_whale = {
            "name": "🧪 تجربة - حوت وهمي",
            "address": "5CQwyYqXJtQqQqW5X8z2vYqXJtQqQqW5X8z2vYqXJtQqQ",
            "note": "هذا إشعار تجريبي للتأكد من عمل البوت",
        }
        await notify_buy(test_whale, test_buy, session, 182.5)
        return  # notify_buy بتبعت الرسالة
    else:
        return  # تجاهل الرسائل العادية

    await send_telegram(reply, session)

# ==================== التحقق من الإعدادات ====================
def check_config() -> bool:
    """التحقق من وجود القيم المطلوبة"""
    ok = True
    if not TELEGRAM_BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN غير موجود في .env")
        ok = False
    if not TELEGRAM_CHAT_ID:
        log.error("❌ TELEGRAM_CHAT_ID غير موجود في .env - ابدأ محادثة مع البوت وبعت /start ثم استخدم @userinfobot")
        ok = False
    if not HELIUS_API_KEY:
        log.warning("⚠️ HELIUS_API_KEY مش موجود - البوت هيستخدم public RPCs (مجاني 100% بس أبطأ)")
        log.warning("💡 علشان تجيب Helius API key مجاني: https://www.helius.dev/")
    else:
        log.info("✅ Helius API key موجود - هيُستخدم كـ primary RPC")
    return ok

# ==================== التشغيل ====================
async def main():
    log.info("🚀 بدء تشغيل بوت تتبع الحيتان")
    if not check_config():
        log.error("الإعدادات ناقصة. عدل .env وحاول تاني.")
        return

    init_db()
    log.info(f"📋 عدد المحافظ المتابعة: {len(get_all_whales())}")
    log.info(f"💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}")
    log.info(f"⏱️ فترة الفحص: كل {POLL_SECONDS} ثانية")

    async with aiohttp.ClientSession() as session:
        # إرسال رسالة تأكيد التشغيل
        await send_telegram(
            f"🚀 <b>البوت اشتغل!</b>\n\n🐋 محافظ متابعة: {len(get_all_whales())}\n💰 حد الشراء: ${MIN_BUY_USD:,.0f}\n\nللتحكم: /help",
            session
        )

        # تشغيل listener الأوامر في الـ background
        asyncio.create_task(handle_telegram_updates(session))

        # حلقة الفحص الرئيسية
        last_sol_price_update = 0
        sol_price = 0
        while True:
            try:
                # تحديث سعر SOL كل 60 ثانية
                if time.time() - last_sol_price_update > 60:
                    new_price = await get_sol_price(session)
                    if new_price > 0:
                        sol_price = new_price
                        last_sol_price_update = time.time()
                        log.info(f"💰 سعر SOL: ${sol_price:.2f}")

                # فحص كل المحافظ بالتوازي (مع تحديد الـ concurrency)
                whales = get_all_whales()
                if whales:
                    tasks = [poll_whale(w, session, sol_price) for w in whales]
                    await asyncio.gather(*tasks, return_exceptions=True)

                await asyncio.sleep(POLL_SECONDS)
            except KeyboardInterrupt:
                log.info("إيقاف البوت...")
                break
            except Exception as e:
                log.error(f"Main loop error: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("تم الإيقاف")
