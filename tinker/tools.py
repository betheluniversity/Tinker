__author__ = 'ejc84332'

# python
import hashlib
import os
import fnmatch
from subprocess import call

# flask
from flask import request
from flask import session
from flask import current_app
from flask import render_template
from flask import json as fjson
import requests

# tinker
import config


def init_user():

    if 'username' not in session.keys():
        get_user()

    if 'groups' not in session.keys():
        get_groups_for_user()

    if 'roles' not in session.keys():
        get_roles()

    if 'top_nav' not in session.keys():
        get_nav()


def get_user():

    if current_app.config['ENVIRON'] == 'prod':
        username = request.environ.get('REMOTE_USER')
    else:
        username = current_app.config['TEST_USER']

    session['username'] = username


def get_groups_for_user(username=None):
    from web_services import read
    if not username:
        username = session['username']
    try:
        user = read(username, "user")
        allowed_groups = user.asset.user.groups
    except AttributeError:
        allowed_groups = ""
    session['groups'] = allowed_groups

    return allowed_groups.split(";")


def get_roles(username=None):
    if not username:
        username = session['username']
    url = current_app.config['API_URL'] + "/username/%s/roles" % username
    r = requests.get(url, auth=(current_app.config['API_USERNAME'], current_app.config['API_PASSWORD']))
    roles = fjson.loads(r.content)
    ret = []
    for key in roles.keys():
        ret.append(roles[key]['userRole'])

    # Manually give 'faculty' privileges.
    # todo lets move this to a cascade group
    # if username == 'ejc84332':
    #    ret.append('FACULTY')
    # if username == 'ces55739':
    #     ret.append('FACULTY')
    if username == 'celanna':
        ret.append('FACULTY')

    session['roles'] = ret

    return ret


def get_nav():
    html = render_template('nav.html', **locals())
    session['top_nav'] = html


# does this go here?
def clear_image_cache(image_path):

    # /academics/faculty/images/lundberg-kelsey.jpg"
    # Make sure image path starts with a slash
    if not image_path.startswith('/'):
        image_path = '/%s' % image_path

    resp = []

    for prefix in ['http://www.bethel.edu', 'https://www.bethel.edu',
                   'http://staging.bethel.edu', 'https://staging.bethel.edu']:
        path = prefix + image_path
        digest = hashlib.sha1(path.encode('utf-8')).hexdigest()
        path = "%s/%s/%s" % (config.THUMBOR_STORAGE_LOCATION.rstrip('/'), digest[:2], digest[2:])
        resp.append(path)
        # remove the file at the path
        # if config.ENVIRON == "prod":
        call(['rm', path])

    # now the result storage
    file_name = image_path.split('/')[-1]
    matches = []
    for root, dirnames, filenames in os.walk(config.THUMBOR_RESULT_STORAGE_LOCATION):
        for filename in fnmatch.filter(filenames, file_name):
            matches.append(os.path.join(root, filename))
    for match in matches:
        call(['rm', match])

    matches.extend(resp)

    return str(matches)