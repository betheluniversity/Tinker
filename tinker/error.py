
#flask
from flask import render_template

#local
from tinker import app


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404


@app.errorhandler(403)
def permission_denied(e):
    return render_template('error/403.html'), 403


@app.errorhandler(503)
def transport_error(e):
    return render_template('error/503.html'), 503