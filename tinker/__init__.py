#python
import os

#flask
from flask import Flask
from tinker.tools import TinkerTools

from flask.ext.sqlalchemy import SQLAlchemy

#flask extensions
from flask.ext.foundation import Foundation
##from flask.ext.cache import Cache

#flask extensions
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from tinker.wufoo import models
from tinker.redirects import models

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

#create logging
if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler(app.config['INSTALL_LOCATION'] + '/error.log')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

tools = TinkerTools(app.config)

#Import routes
import views
from tinker.events.views import event_blueprint
from tinker.wufoo.views import wufoo_blueprint
from tinker.redirects.views import redirect_blueprint
app.register_blueprint(event_blueprint, url_prefix='/event')
app.register_blueprint(wufoo_blueprint, url_prefix='/wufoo')
app.register_blueprint(redirect_blueprint, url_prefix='/redirect')

#Import error handling
import error