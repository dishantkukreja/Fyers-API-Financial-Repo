# config_manager.py
import sqlite3
from datetime import datetime

DB_FILENAME = "option_chain.db"

def init_config_table():
    with sqlite3.connect(DB_FILENAME) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS symbol_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                strikecount INTEGER,
                expiry TEXT,
                updated_at TEXT
            )
        ''')
        conn.commit()

def update_symbol_config(symbol, strikecount, expiry):
    updated_at = datetime.now().isoformat()
    with sqlite3.connect(DB_FILENAME) as conn:
        cur = conn.cursor()
        # Use INSERT OR REPLACE so that the configuration is either created or updated
        cur.execute('''
            INSERT INTO symbol_config (symbol, strikecount, expiry, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
            strikecount=excluded.strikecount,
            expiry=excluded.expiry,
            updated_at=excluded.updated_at
        ''', (symbol, strikecount, expiry, updated_at))
        conn.commit()

def get_symbol_config(symbol):
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM symbol_config WHERE symbol = ?
        ''', (symbol,))
        row = cur.fetchone()
    if row:
        return {
            'symbol': row['symbol'],
            'strikecount': row['strikecount'],
            'expiry': row['expiry'],
            'updated_at': row['updated_at']
        }
    return None

def get_all_configured_symbols():
    import sqlite3
    DB_FILENAME = "option_chain.db"
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM symbol_config")
        rows = cur.fetchall()
    # Return a list of unique symbols
    return list({row['symbol'] for row in rows})
