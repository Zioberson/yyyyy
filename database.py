# database.py
# Operacje na bazie danych
import sqlite3
from datetime import datetime

DB_NAME = "portfolio.db"

def init_db():
    """Inicjalizuje bazę danych i tworzy tabele, jeśli nie istnieją."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Tabela na przechowywanie aktywów
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            asset_type TEXT NOT NULL CHECK(asset_type IN ('kryptowaluta', 'akcja', 'etf', 'waluta', 'surowiec', 'nieruchomosc'))
        );
        """)

        # Tabela na transakcje
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('buy', 'sell')),
            quantity REAL NOT NULL,
            price_per_unit REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        );
        """)
        conn.commit()

def get_or_create_asset(symbol, name, asset_type):
    """Pobiera istniejący zasób lub tworzy nowy, jeśli nie istnieje."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM assets WHERE symbol = ?", (symbol,))
        asset = cursor.fetchone()
        if asset:
            return asset[0]
        else:
            cursor.execute(
                "INSERT INTO assets (symbol, name, asset_type) VALUES (?, ?, ?)",
                (symbol, name, asset_type)
            )
            conn.commit()
            return cursor.lastrowid

def add_transaction(symbol, name, asset_type, transaction_type, quantity, price_per_unit, transaction_date):
    """Dodaje nową transakcję do bazy danych."""
    asset_id = get_or_create_asset(symbol, name, asset_type)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (asset_id, transaction_type, quantity, price_per_unit, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset_id, transaction_type, quantity, price_per_unit, transaction_date)
        )
        conn.commit()
        print(f"Dodano transakcję: {transaction_type} {quantity} {symbol} po cenie {price_per_unit}")

def get_all_transactions():
    """Pobiera wszystkie transakcje z ich aktywami."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Używamy JOIN, aby pobrać również informacje o aktywach
        cursor.execute("""
            SELECT
                t.id,
                a.symbol,
                a.asset_type,
                t.transaction_type,
                t.quantity,
                t.price_per_unit,
                t.transaction_date
            FROM transactions t
            JOIN assets a ON t.asset_id = a.id
            ORDER BY t.transaction_date DESC
        """)
        return cursor.fetchall()

def delete_transaction(transaction_id):
    """Usuwa transakcję o podanym ID."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        print(f"Usunięto transakcję o ID: {transaction_id}")


if __name__ == '__main__':
    print("--- Lista wszystkich transakcji w bazie danych ---")
    init_db()
    all_transactions = get_all_transactions()
    if not all_transactions:
        print("Brak transakcji w bazie danych.")
    else:
        for t in all_transactions:
            print(t)