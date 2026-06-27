"""
بوت تتبع حيتان Meme Coins على Solana
====================================
- بيراقب محافظ الحيتان على شبكة Solana
- بيبعت إشعار فوري على Telegram لما أي حوت يشتري meme coin
- بيجيب بيانات العملة من DexScreener (مجاني)

التشغيل:
  1. python3 -m venv venv && source venv/bin/activate
  2. pip install -r requirements.txt
  3. املأ .env بالقيم (TELEGRAM_CHAT_ID و HELIUS_API_KEY)
  4. python bot.py
"""
import os
import asyncio
import logging
import sqlite3
import time
import json
from typing import Dict, List, Optional, Set
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# ==================== الإعدادات ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()
MIN_BUY_USD = float(os.getenv("MIN_BUY_USD", "500"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))

# Helius RPC URL
HELIUS_RPC = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# قاعدة بيانات SQLite بسيطة (file واحد)
DB_PATH = Path(__file__).parent / "seen.db"

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("whale-bot")

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

# ==================== Helius RPC ====================
async def helius_rpc(session: aiohttp.ClientSession, method: str, params: list) -> Optional[Dict]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        async with session.post(HELIUS_RPC, json=payload, timeout=30) as resp:
            if resp.status != 200:
                log.error(f"Helius {resp.status}: {await resp.text()}")
                return None
            data = await resp.json()
            if "error" in data:
                log.error(f"Helius error: {data['error']}")
                return None
            return data.get("result")
    except Exception as e:
        log.error(f"Helius exception: {e}")
        return None

async def get_recent_signatures(session: aiohttp.ClientSession, address: str, limit: int = 8) -> List[Dict]:
    result = await helius_rpc(session, "getSignaturesForAddress", [address, {"limit": limit}])
    return result if result else []

async def get_parsed_tx(session: aiohttp.ClientSession, signature: str) -> Optional[Dict]:
    result = await helius_rpc(session, "getTransaction",
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

    منطق بسيط:
    - لو فيه transfer لـ WSOL خارج من المحفظة (الحوت دفع SOL)
    - وفي نفس الوقت transfer لـ token جاي للمحفظة (الحوت استلم عملة)
    - يبقى ده "شراء"

    بيرجع:
    {
        "token_mint": str,
        "token_amount": float,
        "sol_amount": float,
        "value_usd": float,  # بنحسبه من سعر SOL
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

        inner_instructions = msg.get("innerInstructions", []) or []
        # نطبق كل الـ token transfers من الـ inner instructions + outer
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
        if not bought_tokens or total_sol_out <= 0:
            return None

        # نختار أكبر token تم شراؤه
        biggest = max(bought_tokens, key=lambda t: t["amount"])
        # تحويل lamports to SOL (token amount بـ uiAmount بالفعل، بس SOL الخام بالـ lamports)
        # sol_diff هنا بالفعل uiAmount (wrapped SOL) - يعني بالـ SOL الحقيقي
        sol_paid = total_sol_out

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

                # فلتر حسب الحد الأدنى
                if value_usd >= MIN_BUY_USD:
                    await notify_buy(whale, buy, session, sol_price)

            # نعلمها كـ seen (سواء شراء أو لأ، علشان ما نفحصهاش تاني)
            mark_seen(sig)

    except Exception as e:
        log.error(f"Error polling {name}: {e}")

async def notify_buy(whale: Dict, buy: Dict, session: aiohttp.ClientSession, sol_price: float):
    """إرسال إشعار شراء على Telegram"""
    name = whale.get("name", "Unknown Whale")
    note = whale.get("note", "")
    token_mint = buy["token_mint"]

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

    # صياغة الرسالة
    usd_str = f"${buy['value_usd']:,.0f}" if buy.get("value_usd") else "؟"
    sol_str = f"{buy['sol_amount']:.2f} SOL"
    price_str = f"${price:.8f}" if price < 0.01 else f"${price:.4f}"
    liq_str = f"${liquidity:,.0f}" if liquidity else "؟"
    vol_str = f"${volume:,.0f}" if volume else "؟"
    mcap_str = f"${mcap:,.0f}" if mcap else "؟"

    text = f"""
🐋 <b>حوت اشترى!</b>

👤 <b>الحوت:</b> {name}
{f"📝 {note}" if note else ""}

🪙 <b>العملة:</b> {symbol} - {token_name}{age_str}
💰 <b>قيمة الشراء:</b> {usd_str} ({sol_str})
📊 <b>السعر:</b> {price_str}
💧 <b>السيولة:</b> {liq_str}
📈 <b>الحجم 24h:</b> {vol_str}
🏷️ <b>Market Cap:</b> {mcap_str}
🔗 <b>DEX:</b> {dex}

🔗 <a href="{url}">DexScreener</a> | <a href="https://solscan.io/tx/{buy['signature']}">Solscan TX</a>
🏦 <a href="https://solscan.io/account/{whale['address']}">المحفظة</a>
"""
    log.info(f"📤 Buy alert: {name} bought {symbol} ({usd_str})")
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
        reply = """🐋 <b>بوت تتبع حيتان Meme Coins</b>

الأوامر:
/list - عرض كل المحافظ المتابعة
/add &lt;address&gt; &lt;name&gt; - إضافة محفظة
/remove &lt;address&gt; - حذف محفظة
/stats - إحصائيات سريعة

البوت بيراقب المحافظ وبيبعتلك إشعار فوري لما أي حوت يشتري meme coin بقيمة فوق الحد الأدنى ($""" + f"{MIN_BUY_USD:,.0f}" + """).
"""
    elif cmd == "/list":
        whales = get_all_whales()
        if not whales:
            reply = "مفيش محافظ في القائمة."
        else:
            reply = f"📋 <b>المحافظ المتابعة ({len(whales)}):</b>\n\n"
            for i, w in enumerate(whales, 1):
                reply += f"{i}. <b>{w.get('name', 'بدون اسم')}</b>\n   <code>{w['address']}</code>\n"
    elif cmd == "/add":
        if len(parts) < 3:
            reply = "الاستخدام: /add <address> <name>\nمثال: /add 5CQw...HFMJ WhaleAlpha"
        else:
            address = parts[1]
            name = " ".join(parts[2:])
            add_user_whale(address, name)
            reply = f"✅ اتضافت المحفظة:\n{name}\n<code>{address}</code>"
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
        conn.close()
        reply = f"📊 <b>إحصائيات</b>\n\n🐋 محافظ متابعة: {whales_count}\n📝 معاملات مرصودة: {count}\n💰 حد الشراء الأدنى: ${MIN_BUY_USD:,.0f}"
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
        log.error("❌ HELIUS_API_KEY غير موجود في .env - سجل من https://www.helius.dev/")
        ok = False
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
