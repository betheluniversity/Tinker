from flask import Flask, render_template, Blueprint, session, abort, request
from tinker import tools
from flask.ext.classy import FlaskView, route
from tinker.admin.cache.CacheController import CacheController

CacheBlueprint = Blueprint('CacheBlueprint', __name__, template_folder='templates')

class CacheClear(FlaskView):
    route_base = '/admin/cache-clear'

    def __init__(self):
        self.base = CacheController()

    def before_request(self, name, **kwargs):
        if 'Administrators' not in session['groups']:
            abort(403)

    def index(self):
        return render_template('cache-home.html', **locals())

    @route("/submit", methods=['post'])
    def submit(self):
        path = request.form['url']
        return self.base.cache_clear(path)

CacheClear.register(CacheBlueprint)
