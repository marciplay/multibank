import sqlite3

def init_db():
    conn = sqlite3.connect('multibank.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    balance REAL,
                    currency TEXT,
                    client_id TEXT,
                    bank_name TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()