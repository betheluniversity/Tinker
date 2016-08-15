
from flask.ext.classy import FlaskView
from flask import Flask, Blueprint
from flask import render_template, send_file

BaseBlueprint = Blueprint('base', __name__, template_folder='templates')


class Base(FlaskView):
    route_base = '/'

    def index(self):
        # index page for adding events and things
        return render_template('home.html', **locals())

    def about(self):
        return render_template('about-page.html', **locals())

    def get_image(self, image_name):
        return send_file('images/' + image_name, mimetype='image/png')

Base.register(BaseBlueprint)
