from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    from flaskr.index import data_display, search_form_display, check_connection
    CORS(app, resources={r"/check_connection": {"origins": "*"}})  # Allow all origins for testing

    app.add_url_rule('/check_connection', endpoint=None, view_func=check_connection, methods=['GET', 'POST'])
    app.add_url_rule('/', endpoint=None, view_func=search_form_display, methods=["GET"])
    app.add_url_rule('/results', endpoint=None, view_func=data_display, methods=["POST"])
    return app


app = create_app()
app.config['SECRET_KEY'] = 'a_secret_string'  #secret key needed to flash()
if __name__ == "__main__":
    app.run(debug=True)
