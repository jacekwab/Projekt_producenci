import sqlite3
import traceback
from datetime import datetime
import sys
import os


def init_db():
    conn = sqlite3.connect("errors.db")
    cursor = conn.cursor()

    # Tworzymy tabelę, jeśli nie istnieje
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                function_name TEXT NOT NULL,
                error_type TEXT NOT NULL,
                custom_message TEXT,
                full_traceback TEXT NOT NULL
            )
        ''')

    conn.commit()  # 🟢 WAŻNE: Upewniamy się, że operacja CREATE TABLE jest zapisana
    conn.close()  # Zamykamy połączenie w każdym przypadku


def log_error(function_name, error, custom_message=None):
    '''Funkcja zapisuje dane dotyczące błędu w bazie danych'''

    conn = sqlite3.connect("errors.db")

    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    full_traceback = traceback.format_exc()

    cursor.execute('''
            INSERT INTO error_logs (timestamp, function_name, error_type, custom_message, full_traceback)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, function_name, error_type, custom_message, full_traceback))

    conn.commit()
    print(f"[LOG ERROR] Zapisano błąd: {error_type} w {function_name}")
    conn.close()


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if exc_type is not None:
        log_error("GLOBAL", exc_value)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def setup_global_exception_logging():
    sys.excepthook = global_exception_handler
