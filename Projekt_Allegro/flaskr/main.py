from flask import Flask

def create_app():

    app = Flask(__name__)
    from index import data_display
    app.add_url_rule('/', endpoint = None, view_func = data_display)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)