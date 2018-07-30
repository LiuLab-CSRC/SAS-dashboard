from werkzeug.wsgi import DispatcherMiddleware

from .dashboard.app import dash_app
from .dashboard.base import DASH_URL_BASE
from .webapp.app import flask_app as sasdash_app

__version__ = '0.1'

def create_app():
    return sasdash_app
# sasdash_app.wsgi_app = DispatcherMiddleware(sasdash_app, {DASH_URL_BASE: dash_app})
