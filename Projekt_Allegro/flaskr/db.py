import sqlite3
import traceback
from datetime import datetime
import sys
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)


class ErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.Text, nullable=False)
    function_name = db.Column(db.Text, nullable=False)
    error_type = db.Column(db.Text, nullable=False)
    custom_message = db.Column(db.Text, nullable=True)
    full_traceback = db.Column(db.Text, nullable=False)


def init_db(app):
    load_dotenv()
    # Hasło admina i katalog bazy danych znajduje się w pliku .env
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")
    database_catalog = os.getenv("DATABASE_CATALOG")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Pobieramy katalog, w którym jest plik
    DB_PATH = os.path.join(BASE_DIR, database_catalog, "database.db")  # Tworzymy pełną ścieżkę
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

        # Tworzenie konta administratora, jeśli nie istnieje
        if not User.query.filter_by(login='admin').first():

            admin_user = User(
                login='admin',
                password_hash=generate_password_hash(admin_password),
                email=admin_email,
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()


def log_error(function_name, error, custom_message=None):
    """Funkcja zapisuje dane dotyczące błędu w bazie danych"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    full_traceback = traceback.format_exc()

    # Tworzymy nowy wpis w bazie
    new_error = ErrorLog(
        timestamp=timestamp,
        function_name=function_name,
        error_type=error_type,
        custom_message=custom_message,
        full_traceback=full_traceback
    )

    try:
        db.session.add(new_error)
        db.session.commit()  # Zapisujemy do bazy
        print(f"[LOG ERROR] Zapisano błąd: {error_type} w {function_name}")
    except Exception as db_error:
        db.session.rollback()  # Cofamy zmiany w razie błędu
        print(f"[LOG ERROR] Błąd zapisu do bazy: {db_error}")


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if exc_type is not None:
        log_error("GLOBAL", exc_value)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def setup_global_exception_logging():
    sys.excepthook = global_exception_handler
