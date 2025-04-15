# db_manager.py
import sqlite3
import json

DB_FILENAME = "option_chain.db"

def init_db():
    with sqlite3.connect(DB_FILENAME) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS option_chain_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp TEXT,
                option_chain TEXT,
                strikecount INTEGER,
                expiry TEXT
            )
        ''')
        conn.commit()

def reset_db():
    with sqlite3.connect(DB_FILENAME) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM option_chain_data")
        conn.commit()

def store_option_chain_data(symbol, timestamp, option_chain, strikecount, expiry):
    with sqlite3.connect(DB_FILENAME) as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO option_chain_data (symbol, timestamp, option_chain, strikecount, expiry)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, timestamp, json.dumps(option_chain), strikecount, expiry))
        conn.commit()

def get_data_from_db(symbol):
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT timestamp, option_chain FROM option_chain_data
            WHERE symbol = ?
            ORDER BY timestamp ASC
        ''', (symbol,))
        rows = cur.fetchall()
    x_data = []
    chain_history = []
    for row in rows:
        x_data.append(row["timestamp"])
        try:
            chain = json.loads(row["option_chain"])
        except Exception:
            chain = []
        chain_history.append(chain)
    return {'x_data': x_data, 'chain_history': chain_history}
