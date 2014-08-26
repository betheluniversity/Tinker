#python
import json
import requests

#flask
from flask import request, Blueprint, render_template, jsonify

#Tinker
from tinker import db
from tinker import cache
from tinker.wufoo.models import FormInfo
from tinker.wufoo import api

wufoo_blueprint = Blueprint('wufoo', __name__,
                        template_folder='templates', static_folder='static')
@wufoo_blueprint.route("/")
def show_manage():

    forms = api.get_form_list()

    return render_template('index.html', **locals())


@wufoo_blueprint.route('/all-preload')
def all_preload():
    forms = json.loads(get_forms())['Forms']
    url = "https://editor.its.bethel.edu/silva/wufoo/wufoo-manager/++rest++wufoo-preload-info?skip-bethel-auth=1&site=betheluniversity&form=%s"
    username = "wufoo-upgrade"
    password = "password"
    site="betheluniversity"
    ret = []
    for form in forms:
        x = 1
        hash = form['Hash']
        request_url = url % hash
        resp = requests.get(request_url, auth=(username, password))
        preload_info = resp.content
        db_row = FormInfo(hash=hash, preload_info=preload_info, paypal_name=None, paypal_budget_number=None, sync_status=False)
        try:
            db.session.add(db_row)
            db.session.commit()
        except:
            db.session.rollback()
            db.session.merge(db_row)
            db.session.commit()
        ret.append(db_row)
    resp = ""
    for item in ret:
        resp += str(item) + "\n"

    return "<pre>%s</pre>" % resp


@wufoo_blueprint.route("/get-forms") #, methods=['POST'])
@cache.cached(timeout=500)
def get_forms():
    return api.get_form_list()


@wufoo_blueprint.route('/embed-form/<formhash>')
def embed_form(formhash):
    formhash = """
    <div id="wufoo-qo8j30m1rat7u1">
Fill out my <a href="https://betheluniversity.wufoo.com/forms/qo8j30m1rat7u1">online form</a>.
</div>
<script type="text/javascript">var qo8j30m1rat7u1;(function(d, t) {
var s = d.createElement(t), options = {
'userName':'betheluniversity',
'formHash':'qo8j30m1rat7u1',
'autoResize':true,
'height':'781',
'async':true,
'host':'wufoo.com',
'header':'show',
'ssl':true};
s.src = ('https:' == d.location.protocol ? 'https://' : 'http://') + 'www.wufoo.com/scripts/embed/form.js';
s.onload = s.onreadystatechange = function() {
var rs = this.readyState; if (rs) if (rs != 'complete') if (rs != 'loaded') return;
try { qo8j30m1rat7u1 = new WufooForm();qo8j30m1rat7u1.initialize(options);qo8j30m1rat7u1.display(); } catch (e) {}};
var scr = d.getElementsByTagName(t)[0], par = scr.parentNode; par.insertBefore(s, scr);
})(document, 'script');</script>
    """
    return formhash


@wufoo_blueprint.route('/load-form/<formhash>')
def load_form(formhash):

    #Load prelaod info for form
    info = FormInfo.query.get(formhash)

    return api.load_form(formhash, form_info=info)


@wufoo_blueprint.route('/preload-save', methods=['POST'])
def preload_save():
    mappings = request.form
    sync_fields = {}
    form_hash = ''
    form_name = ''
    keys = mappings.keys()
    for key in keys:
        value = mappings[key]
        if key.startswith('Field') and value:
            sync_fields[key] = value
        elif key == 'wufoo-form-hash':
            form_hash, form_name = mappings[key].split(":")

    preload_info = json.dumps(sync_fields)

    ##Check if there is an entry in the DB for this form yet
    dbrecord = FormInfo.query.get(form_hash)

    if dbrecord:
        #update existing
        dbrecord.preload_info = preload_info
        db.session.merge(dbrecord)
        db.session.commit()
    else:
        #create new
        info = FormInfo(hash=hash, preload_info=preload_info, paypal_name=None, paypal_budget_number=None, sync_status=False)
        db.session.add(info)
        db.session.commit()


@wufoo_blueprint.route('/get-preload-options')
def get_preload_options():
    supported_names = {'bethel_id': 'Bethel ID',
                       'last_name': 'Last Name',
                       'first_name': 'First Name',
                       'middle_name': 'Middle Name',
                       'bu_email': 'BU Email',
                       'udc_id': 'UDC Id (unique identifier)',
                       'phonetic': 'Phonetic',
                       'majr1': 'Major 1',
                       'majr2': 'Major 2',
                       'majr3': 'Major 3',
                       'majr4': 'Major 4',
                       'majr5': 'Major 5',
                       'department': 'Department',
                       'begtime': 'Ceremony Begin Time',
                       'cermdate': 'Ceremony Date',
                       'CohortUG': 'CAPS Cohort',
                       'CohortGS': 'GS Cohort',
                       'CohortUG1415': 'CAPS Cohort',
                       'CohortGS1415': 'GS Cohort',
                       'Fall13CreditUG': 'CAPS Fall 13 Credit',
                       'Spring14CreditUG': 'CAPS Spring 14 Credit',
                       'Summer14CreditUG': 'CAPS Summer 14 Credit',
                       'Fall13CreditGS': 'GS Fall 13 Credit',
                       'Spring14CreditGS': 'GS Spring 14 Credit',
                       'Summer14CreditGS': 'GS Summer 14 Credit',
                       'Fall14CreditUG': 'CAPS Fall 14 Credit',
                       'Spring15CreditUG': 'CAPS Spring 15 Credit',
                       'Summer15CreditUG': 'CAPS Summer 15 Credit',
                       'Fall14CreditGS': 'GS Fall 14 Credit',
                       'Spring15CreditGS': 'GS Spring 15 Credit',
                       'Summer15CreditGS': 'GS Summer 15 Credit'
                       }

    return jsonify(dict(supported_names))