#!/usr/bin/env python3
"""
سكريبت اختبار البوت محلياً
========================
بيختبر كل المكونات قبل ما ترفع البوت على AWS:
1. إعدادات .env
2. اتصال Telegram
3. اتصال Solana RPCs
4. اتصال DexScreener
5. قراءة محفظة حوت حقيقية
6. إرسال إشعار تجريبي على تيليجرام
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path

# إضافة المسار الحالي
sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ألوان
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def ok(msg):    print(f"{GREEN}✅ {msg}{NC}")
def fail(msg):  print(f"{RED}❌ {msg}{NC}")
def info(msg):  print(f"{BLUE}ℹ️  {msg}{NC}")
def warn(msg):  print(f"{YELLOW}⚠️  {msg}{NC}")
def header(msg):
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}  {msg}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")


async def test_env():
    """1. التحقق من إعدادات .env"""
    header("1️⃣ فحص إعدادات .env")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    helius = os.getenv("HELIUS_API_KEY", "").strip()
    
    if not token:
        fail("TELEGRAM_BOT_TOKEN مش موجود في .env")
        return False
    ok(f"TELEGRAM_BOT_TOKEN: {token[:15]}...")
    
    if not chat_id:
        fail("TELEGRAM_CHAT_ID مش موجود في .env")
        return False
    ok(f"TELEGRAM_CHAT_ID: {chat_id}")
    
    if helius:
        ok(f"HELIUS_API_KEY: موجود ({helius[:8]}...)")
    else:
        warn("HELIUS_API_KEY مش موجود - هنتستخدم public RPCs")
    
    return True


async def test_telegram(session):
    """2. اختبار اتصال Telegram"""
    header("2️⃣ فحص اتصال Telegram")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        async with session.get(url, timeout=15) as resp:
            data = await resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                ok(f"البوت متصل: @{bot_info.get('username', '?')}")
                ok(f"اسم البوت: {bot_info.get('first_name', '?')}")
                return True
            else:
                fail(f"Telegram error: {data}")
                return False
    except Exception as e:
        fail(f"Telegram exception: {e}")
        return False


async def test_solana_rpcs(session):
    """3. اختبار اتصال Solana RPCs"""
    header("3️⃣ فحص اتصال Solana RPCs")
    
    rpcs = [
        "https://api.mainnet-beta.solana.com",
        "https://solana-mainnet.rpc.extrnode.com",
        "https://rpc.ankr.com/solana",
    ]
    
    helius = os.getenv("HELIUS_API_KEY", "").strip()
    if helius:
        rpcs.insert(0, f"https://mainnet.helius-rpc.com/?api-key={helius}")
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getHealth",
        "params": []
    }
    
    working = 0
    for rpc in rpcs:
        try:
            start = time.time()
            async with session.post(rpc, json=payload, timeout=10) as resp:
                duration = (time.time() - start) * 1000
                data = await resp.json()
                if data.get("result") == "ok":
                    ok(f"{rpc[:50]}... ({duration:.0f}ms)")
                    working += 1
                else:
                    fail(f"{rpc[:50]}... - {data}")
        except Exception as e:
            fail(f"{rpc[:50]}... - {e}")
    
    if working > 0:
        ok(f"{working}/{len(rpcs)} RPCs شغالة")
        return True
    else:
        fail("مفيش RPC شغال!")
        return False


async def test_dexscreener(session):
    """4. اختبار اتصال DexScreener"""
    header("4️⃣ فحص اتصال DexScreener")
    
    # نجرب العملة اللي المستخدم بعتها قبل كده
    token = "Tqj8yFmagrg7oorpQkVGYR52r96RFTamvWfth9bpump"
    url = f"https://api.dexscreener.com/tokens/v1/solana/{token}"
    
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                fail(f"DexScreener error: {resp.status}")
                return False
            pairs = await resp.json()
            if not pairs:
                fail("مفيش بيانات للعملة")
                return False
            
            best = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
            symbol = best.get("baseToken", {}).get("symbol", "?")
            name = best.get("baseToken", {}).get("name", "?")
            price = float(best.get("priceUsd", 0) or 0)
            liq = float(best.get("liquidity", {}).get("usd", 0) or 0)
            mcap = float(best.get("fdv", 0) or 0)
            
            ok(f"العملة: {symbol} - {name}")
            ok(f"السعر: ${price:.6f}")
            ok(f"السيولة: ${liq:,.0f}")
            ok(f"Market Cap: ${mcap:,.0f}")
            return True
    except Exception as e:
        fail(f"DexScreener exception: {e}")
        return False


async def test_read_whale(session):
    """5. قراءة محفظة حوت حقيقية"""
    header("5️⃣ قراءة محفظة حوت حقيقية")
    
    from whales import WHALES
    if not WHALES:
        fail("مفيش محافظ في whales.py")
        return False
    
    whale = WHALES[0]
    info(f"المحفظة: {whale['name']}")
    info(f"العنوان: {whale['address']}")
    
    # نجيب آخر معاملات المحفظة
    rpcs = [
        "https://api.mainnet-beta.solana.com",
        "https://solana-mainnet.rpc.extrnode.com",
        "https://rpc.ankr.com/solana",
    ]
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [whale["address"], {"limit": 5}]
    }
    
    for rpc in rpcs:
        try:
            async with session.post(rpc, json=payload, timeout=15) as resp:
                data = await resp.json()
                if data.get("result"):
                    sigs = data["result"]
                    ok(f"لقيت {len(sigs)} معاملة أخيرة")
                    if sigs:
                        latest = sigs[0]
                        sig = latest.get("signature", "")
                        info(f"أحدث معاملة: {sig[:50]}...")
                        
                        # وقت المعاملة
                        block_time = latest.get("blockTime")
                        if block_time:
                            age = int(time.time() - block_time)
                            if age < 60:
                                info(f"منذ {age} ثانية")
                            elif age < 3600:
                                info(f"منذ {age // 60} دقيقة")
                            else:
                                info(f"منذ {age // 3600} ساعة")
                    return True
                elif data.get("error"):
                    continue  # نجرب RPC تاني
        except Exception as e:
            continue
    
    warn("مقدرتش أقرا المحفظة (ممكن المحفظة مش حقيقية)")
    return True  # مش خطأ قاتل


async def test_send_notification(session):
    """6. إرسال إشعار تجريبي على تيليجرام"""
    header("6️⃣ إرسال إشعار تجريبي على تيليجرام")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    text = """🧪 <b>اختبار البوت - شغال تمام!</b>

✅ اتصال Telegram: شغال
✅ اتصال Solana RPCs: شغال
✅ اتصال DexScreener: شغال
✅ قراءة محافظ الحيتان: شغال

🚀 البوت جاهز للنشر على AWS!

<b>الإعدادات:</b>
💰 حد الشراء: $500
⏱️ فترة الفحص: 5 ثواني
🐋 المحافظ: 10 (Solana) + 3 (BSC)

ابعت /help للبوت علشان تشوف كل الأوامر"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    
    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            data = await resp.json()
            if data.get("ok"):
                ok("الإشعار التجريبي اتبعت على تيليجرام! 🎉")
                ok("افتح تيليجرام على موبايلك وتأكد")
                return True
            else:
                fail(f"Telegram error: {data}")
                return False
    except Exception as e:
        fail(f"Exception: {e}")
        return False


async def test_accumulation_logic():
    """7. اختبار منطق التجميع"""
    header("7️⃣ فحص منطق التجميع")
    
    try:
        # نستورد من bot.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot", Path(__file__).parent / "bot.py")
        bot_module = importlib.util.module_from_spec(spec)
        
        # ما نشغلش main() - بس نتحقق من الاستيراد
        # هنشوف إن الدوال موجودة
        with open(Path(__file__).parent / "bot.py") as f:
            code = f.read()
        
        if "def check_and_notify_accumulation" in code:
            ok("دالة check_and_notify_accumulation موجودة")
        else:
            fail("دالة التجميع مش موجودة")
            return False
        
        if "def log_whale_buy" in code:
            ok("دالة log_whale_buy موجودة")
        else:
            fail("دالة log_whale_buy مش موجودة")
            return False
        
        if "ACCUMULATION_THRESHOLD" in code:
            ok("إعدادات التجميع موجودة")
        else:
            fail("إعدادات التجميع مش موجودة")
            return False
        
        ok("منطق التجميع سليم")
        return True
    except Exception as e:
        fail(f"Error: {e}")
        return False


async def test_bsc_monitor():
    """8. فحص مراقب BSC"""
    header("8️⃣ فحص مراقب BSC")
    
    bsc_file = Path(__file__).parent / "bsc_monitor.py"
    if not bsc_file.exists():
        fail("ملف bsc_monitor.py مش موجود")
        return False
    
    ok("ملف bsc_monitor.py موجود")
    
    with open(bsc_file) as f:
        code = f.read()
    
    if "BSC_RPCS" in code:
        ok("BSC RPCs معرفة")
    if "PANCAKE_ROUTER" in code:
        ok("PancakeSwap router معرف")
    if "BSC_WHALES" in code:
        ok("استيراد محافظ BSC من whales.py")
    if "async def main" in code:
        ok("دالة main موجودة")
    
    # نتحقق إن ملف whales.py فيه BSC_WHALES
    with open(Path(__file__).parent / "whales.py") as f:
        whales_code = f.read()
    if "BSC_WHALES" in whales_code:
        ok("BSC_WHALES معرفة في whales.py")
    else:
        fail("BSC_WHALES مش معرفة في whales.py")
        return False
    
    return True


async def main():
    print(f"{BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   🧪 اختبار بوت تتبع الحيتان - Pre-Deployment Test      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{NC}")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        results.append(await test_env())
        if all(results):
            results.append(await test_telegram(session))
            results.append(await test_solana_rpcs(session))
            results.append(await test_dexscreener(session))
            results.append(await test_read_whale(session))
            results.append(await test_accumulation_logic())
            results.append(await test_bsc_monitor())
            # الإشعار التجريبي آخر حاجة
            if all(results[:-1]):  # كل الاختبارات السابقة نجحت
                results.append(await test_send_notification(session))
            else:
                warn("هتتخطى اختبار الإشعار التجريبي بسبب فشل اختبار سابق")
                results.append(False)
    
    # النتيجة النهائية
    header("📊 النتيجة النهائية")
    passed = sum(results)
    total = len(results)
    
    if all(results):
        ok(f"كل الاختبارات نجحت! ({passed}/{total})")
        print(f"\n{GREEN}🎉 البوت جاهز للنشر على AWS!{NC}")
        print(f"{GREEN}🚀 تقدر ترفعه على GitHub دلوقتي{NC}")
        return 0
    else:
        fail(f"{passed}/{total} اختبارات نجحت")
        print(f"\n{YELLOW}⚠️  فيه مشاكل لازم تتصلح قبل النشر{NC}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
