"""
قاعدة بيانات SQLite
===================
تحفظ:
- المعاملات اللي اتبعتت بالفعل (علشان ما نبعتش نفس الإشعار مرتين)
- تاريخ عمليات الحيتان (للملخص الدوري وكشف التجميع)
"""
import sqlite3
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from config import config


def init_db():
    """إنشاء الجداول لو مش موجودة"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS seen_transactions (
                signature TEXT PRIMARY KEY,
                whale_address TEXT NOT NULL,
                token_address TEXT NOT NULL,
                seen_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS whale_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whale_address TEXT NOT NULL,
                token_address TEXT NOT NULL,
                token_symbol TEXT,
                action TEXT NOT NULL,  -- 'buy' or 'sell'
                amount_usd REAL,
                amount_sol REAL,
                amount_tokens REAL,
                is_early_entry INTEGER DEFAULT 0,
                timestamp INTEGER NOT NULL,
                signature TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_activity_token
                ON whale_activity(token_address, timestamp);

            CREATE INDEX IF NOT EXISTS idx_activity_whale
                ON whale_activity(whale_address, timestamp);

            CREATE TABLE IF NOT EXISTS user_whales (
                address TEXT PRIMARY KEY,
                name TEXT,
                added_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS blacklisted_tokens (
                address TEXT PRIMARY KEY,
                reason TEXT
            );
        """)


@contextmanager
def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def is_seen(signature: str) -> bool:
    """هل المعاملة دي اتبعتت قبل كده؟"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_transactions WHERE signature = ?",
            (signature,)
        ).fetchone()
        return row is not None


def mark_seen(signature: str, whale_address: str, token_address: str):
    """تعليم المعاملة بأنها اتبعتت"""
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO seen_transactions
               (signature, whale_address, token_address, seen_at)
               VALUES (?, ?, ?, ?)""",
            (signature, whale_address, token_address, int(time.time()))
        )


def log_activity(activity: Dict[str, Any]):
    """تسجيل نشاط حوت في قاعدة البيانات"""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO whale_activity
               (whale_address, token_address, token_symbol, action,
                amount_usd, amount_sol, amount_tokens, is_early_entry,
                timestamp, signature)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                activity["whale_address"],
                activity["token_address"],
                activity.get("token_symbol", ""),
                activity["action"],
                activity.get("amount_usd", 0),
                activity.get("amount_sol", 0),
                activity.get("amount_tokens", 0),
                1 if activity.get("is_early_entry") else 0,
                activity["timestamp"],
                activity.get("signature", ""),
            )
        )


def get_recent_activity_for_token(token_address: str, hours: int) -> List[Dict]:
    """كل نشاط حيتان على عملة معينة في آخر X ساعة"""
    cutoff = int(time.time()) - (hours * 3600)
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT whale_address, token_symbol, action,
                      amount_usd, timestamp, is_early_entry
               FROM whale_activity
               WHERE token_address = ? AND timestamp >= ?
               ORDER BY timestamp DESC""",
            (token_address, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]


def get_unique_whales_for_token(token_address: str, hours: int) -> int:
    """عدد الحيتان الفريدين اللي اشتروا العملة في آخر X ساعة"""
    cutoff = int(time.time()) - (hours * 3600)
    with get_db() as conn:
        row = conn.execute(
            """SELECT COUNT(DISTINCT whale_address) as cnt
               FROM whale_activity
               WHERE token_address = ? AND action = 'buy' AND timestamp >= ?""",
            (token_address, cutoff)
        ).fetchone()
        return row["cnt"] if row else 0


def get_activity_summary(hours: int) -> List[Dict]:
    """ملخص كل النشاط في آخر X ساعة (للملخص الدوري)"""
    cutoff = int(time.time()) - (hours * 3600)
    with get_db() as conn:
        rows = conn.execute(
            """SELECT whale_address, token_address, token_symbol, action,
                      SUM(amount_usd) as total_usd,
                      SUM(amount_sol) as total_sol,
                      COUNT(*) as tx_count,
                      MAX(is_early_entry) as has_early,
                      MAX(timestamp) as last_seen
               FROM whale_activity
               WHERE timestamp >= ?
               GROUP BY whale_address, token_address, action
               ORDER BY last_seen DESC""",
            (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_user_whale(address: str, name: str):
    """إضافة محفظة حوت من المستخدم"""
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_whales (address, name, added_at)
               VALUES (?, ?, ?)""",
            (address, name, int(time.time()))
        )


def remove_user_whale(address: str) -> bool:
    """حذف محفظة حوت من المستخدم"""
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM user_whales WHERE address = ?", (address,)
        )
        return cur.rowcount > 0


def get_all_user_whales() -> List[Dict]:
    """كل المحافظ اللي ضافها المستخدم"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT address, name FROM user_whales"
        ).fetchall()
        return [dict(r) for r in rows]


def blacklist_token(address: str, reason: str):
    """إضافة عملة للقائمة السوداء"""
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO blacklisted_tokens (address, reason)
               VALUES (?, ?)""",
            (address, reason)
        )


def is_blacklisted_token(address: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM blacklisted_tokens WHERE address = ?",
            (address,)
        ).fetchone()
        return row is not None
