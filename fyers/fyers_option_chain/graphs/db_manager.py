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
        cur.execute('CREATE INDEX IF NOT EXISTS idx_symbol_ts ON option_chain_data(symbol, timestamp)')
        conn.commit()

def reset_db():
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.cursor().execute("DELETE FROM option_chain_data")
        conn.commit()

def store_option_chain_data(symbol, timestamp, option_chain_json, strikecount, expiry):
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.cursor().execute(
            "INSERT INTO option_chain_data(symbol, timestamp, option_chain, strikecount, expiry) VALUES (?,?,?,?,?)",
            (symbol, timestamp, option_chain_json, strikecount, expiry)
        )
        conn.commit()


def get_recent_data(symbol, limit=500):
    """
    Return up to `limit` most recent rows for `symbol`,
    newest last (so you can plot in time order).
    """
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # get the last `limit` rows by timestamp
        cur.execute("""
            SELECT timestamp, option_chain
              FROM (
                   SELECT timestamp, option_chain
                     FROM option_chain_data
                    WHERE symbol=?
                 ORDER BY timestamp DESC
                   LIMIT ?
                  )
         ORDER BY timestamp ASC
        """, (symbol, limit))
        rows = cur.fetchall()

    # parse the JSON chains back into lists
    return [
        {'timestamp': r['timestamp'],
         'chain':     json.loads(r['option_chain'])}
        for r in rows
    ]


def get_data_from_db(symbol):
    with sqlite3.connect(DB_FILENAME) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(
            "SELECT timestamp, option_chain FROM option_chain_data WHERE symbol=? ORDER BY timestamp",
            (symbol,)
        ).fetchall()
    return [{'timestamp': r['timestamp'], 'chain': __import__('json').loads(r['option_chain'])} for r in rows]
