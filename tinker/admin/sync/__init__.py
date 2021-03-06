# Global
import json
from datetime import datetime

# Packages
from flask import abort, render_template, request
from flask_classy import FlaskView, route
from xml.etree import ElementTree as ET

# Local
from tinker import app, cache
from tinker.admin.sync.sync_metadata import data_to_add
from tinker.admin.sync.sync_controller import SyncController
from tinker.tinker_controller import admin_permissions, requires_auth
from bu_cascade.asset_tools import update


class SyncView(FlaskView):
    route_base = '/admin/sync'

    def __init__(self):
        self.base = SyncController()

    def before_request(self, name, **kwargs):
        admin_permissions(self)

    def index(self):
        # get the most recent code
        self.base.git_pull()

        metadata_sets_mapping = self.base.get_metadata_sets_mapping()
        data_definition_mapping = self.base.get_data_definitions_mapping()
        mapping_key_values = self.base.get_mapping_keys()

        return render_template('admin/sync/home.html', **locals())

    @route("/all", methods=['post'])
    def all(self):
        # get the most recent code\
        self.base.git_pull()

        data = data_to_add
        returned_keys = []

        # Get id's and names of md sets and data definitions
        metadata_sets_mapping = self.base.get_metadata_sets_mapping()
        data_definition_mapping = self.base.get_data_definitions_mapping()

        # sync
        returned_keys.extend(self.base.sync_metadata_sets(metadata_sets_mapping))
        returned_keys.extend(self.base.sync_data_definitions(data_definition_mapping))

        return render_template('admin/sync/data.html', **locals())

    @route("/metadata", methods=['post'])
    def metadata(self):
        data = json.loads(request.data)
        id = data['id']
        if not isinstance(id, str):
            return abort(400)
        data = data_to_add

        # Get id's and names of md sets and data definitions
        metadata_sets_mapping = self.base.get_metadata_sets_mapping()
        data_definition_mapping = self.base.get_data_definitions_mapping()

        # sync
        returned_keys = self.base.sync_metadata_set(id)

        return render_template('admin/sync/data.html', **locals())

    @route("/datadefinition", methods=['post'])
    def datadefinition(self):
        data = json.loads(request.data)
        id = data['id']
        if not isinstance(id, str):
            return abort(400)
        data = data_to_add

        # Get id's and names of md sets and data definitions
        metadata_sets_mapping = self.base.get_metadata_sets_mapping()
        data_definition_mapping = self.base.get_data_definitions_mapping()

        # sync
        returned_keys = self.base.sync_data_definition(id)

        return render_template('admin/sync/data.html', **locals())

    @requires_auth
    @route("/public/sync-prayer-and-memorial", methods=['get'])
    def sync_prayer_and_memorial(self):
        # read in xml
        resp = self.base.tinker_requests(app.config['PRAYER_AND_MEMORIAL_XML'])
        xml = ET.fromstring(resp.content)

        for block in xml.findall('.//system-block'):
            activated = block.find('.//activated')
            date = block.find('.//publication-date')

            try:
                block_date = datetime.fromtimestamp(int(date.text.strip()) / 1000)
                # for each that is activated and more than 10 days old, deactivate it
                if activated.text.lower() == 'activated' and (datetime.now() - block_date).days > 7:
                    block_asset = self.base.read_block(block.attrib.get('id'))
                    update(block_asset.asset, 'activated', 'Deactivated')
                    block_asset.edit_asset(block_asset.asset)
            except:
                pass

        # publish xml
        self.base.publish(app.config['PRAYER_AND_MEMORIAL_ID'])

        return 'success'
