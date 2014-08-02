#python
import os

#flask
from flask import Flask
from tinker.tools import TinkerTools
#flask extensions
from flask.ext.foundation import Foundation
##from flask.ext.cache import Cache


app = Flask(__name__)
app.config.from_object('config')
##cache = Cache(app, config={'CACHE_TYPE': 'simple'})

##cache.init_app(app)


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
from tinker.events import views
app.register_blueprint(views.event_blueprint, url_prefix='/event')
#Import error handling
import error