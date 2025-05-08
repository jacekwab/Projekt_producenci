from flask import Flask
from flask_cors import CORS
from db import setup_global_exception_logging, init_db
import time
from flaskr.index import data_display, search_form_display, check_connection
from flaskr.user_manage import login_user, register_user, logout
def create_app():
    app = Flask(__name__)
    # Inicjalizacja bazy danych i ustawienie globalnego logowania błędów
    init_db(app)
    setup_global_exception_logging()

    CORS(app, resources={r"/check_connection": {"origins": "*"}})  # Allow all origins for testing

    app.add_url_rule('/check_connection', endpoint=None, view_func=check_connection, methods=['GET', 'POST'])
    app.add_url_rule('/', endpoint=None, view_func=search_form_display, methods=["GET"])
    app.add_url_rule('/results', endpoint=None, view_func=data_display, methods=["POST"])
    app.add_url_rule('/login_user', endpoint=None, view_func=login_user, methods=['GET', 'POST'])
    app.add_url_rule('/logout', endpoint=None, view_func=logout, methods=['GET', 'POST'])
    app.add_url_rule('/register_user', endpoint=None, view_func=register_user, methods=['GET', 'POST'])
    return app


app = create_app()
app.config['SECRET_KEY'] = 'a_secret_string'  #secret key needed to flash()
if __name__ == "__main__":
    app.run(debug=True)
