from __future__ import print_function, division

from string import ascii_letters
from random import choice

from flask import Flask
from flask_bootstrap import Bootstrap

from .views import index, playground, features, exp_pages


def init_blueprint(app):
    app.register_blueprint(index)
    app.register_blueprint(exp_pages)
    app.register_blueprint(playground)
    app.register_blueprint(features)


def create_app(flask_config=None):
    app = Flask(__name__, instance_relative_config=True)
    # app = Flask(__name__.split('.')[0], instance_relative_config=True)

    secret_key = ''.join((choice(ascii_letters) for _ in range(10)))
    default_config = {
        'DEBUG': True,
        'CSRF_ENABLED': True,
        'SECRET_KEY': secret_key,
    }
    app.config.from_mapping(default_config)
    if flask_config is None:
        try:
            app.config.from_pyfile('config.py')
        except FileNotFoundError:
            pass
    else:
        app.config.from_object(flask_config)
    app.url_map.strict_slashes = False

    init_blueprint(app)
    Bootstrap(app)

    if app.debug:
        print('SECRET_KEY:', app.config['SECRET_KEY'])
        print(app.url_map)

    return app


flask_app = create_app()
