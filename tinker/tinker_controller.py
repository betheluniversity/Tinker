import urllib2
import re
import time
from functools import wraps
from xml.etree import ElementTree as ET
import requests
import datetime

# flask
from flask import request
from flask import session
from flask import current_app
from flask import render_template
from flask import json as fjson
from flask import Response

from bu_cascade.cascade_connector import Cascade
from bu_cascade.assets.block import Block
from bu_cascade.assets.page import Page
from bu_cascade import asset_tools
from bu_cascade.asset_tools import update, find

from config.config import SOAP_URL, CASCADE_LOGIN as AUTH, SITE_ID

from tinker import app
from tinker import sentry

def should_be_able_to_edit_image(roles):
    if 'FACULTY-CAS' in roles or 'FACULTY-BSSP' in roles or 'FACULTY-BSSD' in roles:
        return False
    else:
        return True


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == app.config['CASCADE_LOGIN']['username'] and password == app.config['CASCADE_LOGIN']['password']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# def can_user_access_asset( username, id, type):
#     try:
#         user = read(username, "user")
#         allowed_groups = user.asset.user.groups
#     except AttributeError:
#        allowed_groups = ""
#     user_groups = allowed_groups.split(";")
#
#     response = read_access_rights(id, type)['accessRightsInformation']['aclEntries']['aclEntry']
#     response = [right['name'] for right in response]
#
#     if username in response or set(user_groups).intersection(set(response)):
#         return True
#     else:
#         return False


class TinkerController(object):
    def __init__(self):
        self.cascade_connector = Cascade(SOAP_URL, AUTH, SITE_ID)
        self.datetime_format = "%B %d  %Y, %I:%M %p"

    def before_request(self):
        def init_user():

            dev = current_app.config['ENVIRON'] != 'prod'

            if dev:
                session.clear()

            if 'username' not in session.keys():
                get_user()

            if 'groups' not in session.keys():
                get_groups_for_user()

            if 'roles' not in session.keys():
                get_roles()

            if 'top_nav' not in session.keys():
                get_nav()

            if 'user_email' not in session.keys():
                # todo, get prefered email (alias) from wsapi once its added.
                session['user_email'] = session['username'] + "@bethel.edu"

            if 'name' not in session.keys():
                get_users_name()

        def get_user():

            if current_app.config['ENVIRON'] == 'prod':
                username = request.environ.get('REMOTE_USER')
            else:
                username = current_app.config['TEST_USER']

            session['username'] = username

        def get_users_name(username=None):
            if not username:
                username = session['username']
            url = current_app.config['API_URL'] + "/username/%s/names" % username
            r = requests.get(url)
            names = fjson.loads(r.content)['0']
            if names['prefFirstName']:
                fname = names['prefFirstName']
            else:
                fname = names['firstName']
            lname = names['lastName']

            session['name'] = "%s %s" % (fname, lname)

        def get_groups_for_user(username=None):

            # temporary
            # from tinker.tinker_controller import TinkerController
            # base = TinkerController()


            if not username:
                username = session['username']
            try:
                user = self.read(username, "user")
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

        init_user()
        get_nav()

    def log_sentry(self, message, response):

        username = session['username']
        log_time = time.strftime("%c")
        response = str(response)

        sentry.client.extra_context({
            'Time': log_time,
            'Author': username,
            'Response': response
        })

        # log generic message to Sentry for counting
        app.logger.info(message)
        # more detailed message to debug text log
        app.logger.debug("%s: %s: %s %s" % (log_time, message, username, response))

    def inspect_child(self, child):
        # interface method
        pass

    def traverse_xml(self, xml_url, type_to_find):

        response = urllib2.urlopen(xml_url)
        form_xml = ET.fromstring(response.read())

        matches = []
        for child in form_xml.findall('.//' + type_to_find):
                match = self.inspect_child(child)
                if match:
                    matches.append(match)

        # Todo: maybe add some parameter as a search?
        # sort by created-on date.
        matches = sorted(matches, key=lambda k: k['created-on'])

        return matches

    def date_to_java_unix(self, date, datetime_format=None):

        if not datetime_format:
            datetime_format = self.datetime_format

        date = (datetime.datetime.strptime(date, datetime_format))

        # if this is a time field with no date, the  year  will be 1900, and strftime("%s") will return -1000
        if date.year == 1900:
            date = date.replace(year=datetime.date.today().year)

        return int(date.strftime("%s")) * 1000

    def java_unix_to_date(self, date, date_format=None):
        if not date_format:
            date_format = self.datetime_format
        return datetime.datetime.fromtimestamp(int(date) / 1000).strftime(date_format)

    def inspect_sdata_node(self, node):

        node_type = node['type']

        if node_type =='group':
            group = {}
            for n in node['structuredDataNodes']['structuredDataNode']:
                node_identifier = n['identifier'].replace('-', '_')
                group[node_identifier] = self.inspect_sdata_node(n)
            return group

        elif node_type == 'text':
            has_text = 'text' in node.keys() and node['text']
            if not has_text:
                return
            try:
                # todo move
                import datetime
                date = datetime.datetime.strptime(node['text'], '%m-%d-%Y')
                if not date:
                    date = ''
                return date
            except ValueError:
                pass

            try:
                date = self.java_unix_to_date(node['text'])
                if not date:
                    date = ''
                return date
            except TypeError:
                pass
            except ValueError:
                pass

            # A fix to remove the &#160; character from appearing (non-breaking whitespace)
            # Cascade includes this, for whatever reason.
            return node['text'].replace('&amp;#160;', ' ')

    def get_edit_data(self, sdata, mdata, multiple=[]):
        """ Takes in data from a Cascade connector 'read' and turns into a dict of key:value pairs for a form."""
        edit_data = {}

        for node in find(sdata, 'identifier'):
            if node['identifier'] in multiple:

                ## x =  node['identifier']

                nodes = find(sdata, node['identifier'])
                edit_data[node['identifier']] = []
                # todo fix for if  there is only 1 in group. doesn't return list.
                for node in nodes:
                    edit_data[node['identifier']].append(self.inspect_sdata_node(node))
            else:
                node_identifier = node['identifier'].replace('-', '_')
                edit_data[node_identifier] = self.inspect_sdata_node(node)

        dynamic_fields = find(mdata, 'fieldValues')
        # now metadata dynamic fields
        for field in dynamic_fields:
            if find(field, 'fieldValue'):
                items = [find(item, 'value') for item in find(field, 'fieldValue')]
                edit_data[field['name'].replace('-', '_')] = items

        # Add the rest of the fields. Can't loop over these kinds of metadata
        edit_data['title'] = mdata['title']

        return edit_data

    def create_block(self, asset):
        b = Block(self.cascade_connector, asset=asset)
        return b

    def read(self, path_or_id, type):
        return self.cascade_connector.read(path_or_id, type)

    def read_block(self, path_or_id):
        b = Block(self.cascade_connector, path_or_id)
        return b

    def read_page(self, path_or_id):
        p = Page(self.cascade_connector, path_or_id)
        p.read_asset()
        return p.structured_data()

    def publish(self, path_or_id, asset_type='page'):
        return self.cascade_connector.publish(path_or_id, asset_type)

    def unpublish(self, path_or_id, asset_type):
        return self.cascade_connector.unpublish(path_or_id, asset_type)

    def rename(self):
        pass

    def move(self, page_id, destination_path, type='page'):
        return self.cascade_connector.move(page_id, destination_path, type)

    def delete(self, path_or_id, asset_type):
        return self.cascade_connector.delete(path_or_id, asset_type)

    def asset_in_workflow(self, asset_id, asset_type="page"):
        return self.cascade_connector.is_in_workflow(asset_id, asset_type=asset_type)

    def format_title(self, title):
        #todo do we modify titles like this a lot of places?
        title = title.lower().replace(' ', '-')
        title = re.sub(r'[^a-zA-Z0-9-]', '', title)
        return title

    def convert_month_num_to_name(self, month_num):
        return datetime.datetime.strptime(month_num, "%m").strftime("%B").lower()

    def create_folder(self, folder_path):

        if folder_path[0] != "/":
            folder_path = "/%s" % folder_path

        old_folder_asset = self.read(folder_path, "folder")

        if old_folder_asset['success'] == 'false':
            array = folder_path.rsplit("/", 1)
            parent_path = array[0]
            name = array[1]

            asset = {
                'folder': {
                    'metadata': {
                        'title': name
                    },
                    'metadataSetPath': "Basic",
                    'name': name,
                    'parentFolderPath': parent_path,
                    'siteName': "Public"
                }
            }

            return self.cascade_connector.create(asset)
        return old_folder_asset

    def update_asset(self, asset, data):

        for key, value in data.iteritems():
            update(asset, key, value)

        return True

    def add_workflow_to_asset(self, workflow, data):
        data['workflowConfiguration'] = workflow
