from flask import Flask

def create_app():

    app = Flask(__name__)
    from flaskr.index import data_display, search_form_display
    app.add_url_rule('/', endpoint=None, view_func=search_form_display, methods=["GET"])
    app.add_url_rule('/results', endpoint = None, view_func = data_display, methods=["POST"])
    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True)