import sqlite3

def init_db():
    conn = sqlite3.connect('tarot_bot.db')
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            birth_date TEXT,
            wallet_balance INTEGER DEFAULT 0
        )
    ''')

    # Таблица раскладов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spreads (
            spread_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            spread_name TEXT,
            cards TEXT,
            question TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()