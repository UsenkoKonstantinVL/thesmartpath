import logging

from flask import Flask
from flask_restful import Api


from config import config
from rest.errors import errors
from rest.routes import initialize_routes

cfg = config.Config()


def make_app():
    app = Flask(__name__)
    app.config.from_object(cfg)

    api = Api(app, errors=errors)
    initialize_routes(api)

    return app


def main():
    if not cfg.DEBUG:
        logging.getLogger('werkzeug').disabled = True

    app = make_app()
    app.run()


if __name__ == "__main__":
    main()
