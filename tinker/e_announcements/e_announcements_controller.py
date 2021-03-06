# Global
from datetime import datetime
from bu_cascade.asset_tools import find, convert_asset
import math

# Packages
from bu_cascade.asset_tools import update
from flask import session

# Local
from tinker import app, cache
from tinker.tinker_controller import TinkerController


class EAnnouncementsController(TinkerController):

    def __init__(self):
        super(EAnnouncementsController, self).__init__()
        self.brm = [
            'CAS',
            'CAPS',
            'GS',
            'BSSP-TRADITIONAL',
            'BSSP-DISTANCE',
            'BSSD-TRADITIONAL',
            'BSSD-DISTANCE',
            'BSOE-TRADITIONAL',
            'BSOE-DISTANCE',
            'CAS',
            'CAPS',
            'GS',
            'BSSP',
            'BSSD',
            'St. Paul',
            'San Diego'
        ]

    def inspect_child(self, child, find_all=False, csv=False):
        # if find_all is true, then skip the check to see if you are allowed to see it.
        if find_all:
            try:
                return self._iterate_child_xml(child, '')
            except AttributeError:
                # not a valid e-ann block
                return None

        try:
            author = child.find('author').text
            author = author.replace(' ', '').split(',')
        except AttributeError:
            author = []
        if author == []:
            author = child.find('created-by').text
        username = session['username']

        if (author is not None and username in author) or 'E-Announcement Approver' in session['groups']:
            try:
                return self._iterate_child_xml(child, author)
            except AttributeError:
                # not a valid e-ann block
                return None
        else:
            return None

    def _iterate_child_xml(self, child, author=None):

        first = child.find('system-data-structure/first-date').text
        second = child.find('system-data-structure/second-date').text
        first_date_object = datetime.strptime(first, '%m-%d-%Y')
        first_date = first_date_object.strftime('%A %B %d, %Y')
        first_date_past = first_date_object < datetime.now()

        second_date = ''
        second_date_past = ''
        if second:
            second_date_object = datetime.strptime(second, '%m-%d-%Y')
            second_date = second_date_object.strftime('%A %B %d, %Y')
            second_date_past = second_date_object < datetime.now()

        roles = []
        elements = child.findall('.//dynamic-metadata')
        for element in elements:
            for value in element:
                if value.tag == 'value':
                    roles.append(value.text)

        try:
            workflow_status = child.find('workflow').find('status').text
        except AttributeError:
            workflow_status = None

        page_values = {
            'author': author,
            'id': child.attrib['id'] or "",
            'title': child.find('title').text or None,
            'created-on': child.find('created-on').text or None,
            'force-top': child.find('system-data-structure/force-top').text or "",
            'first_date': first_date,
            'second_date': second_date,
            'roles': roles,
            'workflow_status': workflow_status,
            'first_date_past': first_date_past,
            'second_date_past': second_date_past,
            'message': self.element_tree_to_html(child.find('system-data-structure').find('message')) or None
        }
        return page_values

    def validate_form(self, rform):
        from tinker.e_announcements.forms import EAnnouncementsForm

        form = EAnnouncementsForm(rform)

        return form, form.validate_on_submit()

    def update_structure(self, e_announcement_data, rform, e_announcement_id=None):
        # clean up the bytes
        e_announcement_data = convert_asset(e_announcement_data)

        add_data = self.get_add_data(['banner_roles'], rform)

        # create workflow
        workflow = self.create_workflow(app.config['E_ANNOUNCEMENTS_WORKFLOW_ID'], add_data['title'])
        self.add_workflow_to_asset(workflow, e_announcement_data)

        # if parent folder ID exists it will use that over path
        add_data['parentFolderId'] = ''
        if not app.config['UNIT_TESTING']:
            add_data['parentFolderPath'] = self.get_e_announcement_parent_folder(add_data['first_date'])
        else:
            add_data['parentFolderPath'] = "/_testing/philip-gibbens/e-annz-tests"

        # todo, update these to have _ instead of - in Cascade so we don't have to translate
        add_data['email'] = session['user_email']
        add_data['banner-roles'] = add_data['banner_roles']
        add_data['first-date'] = add_data['first_date']
        add_data['second-date'] = add_data['second_date']

        # add id
        if e_announcement_id:
            add_data['id'] = e_announcement_id

        add_data['submitter_name'] = session['name']

        self.update_asset(e_announcement_data, add_data)

        # for some reason, title is not already set, so it must be set manually
        e_announcement_data['xhtmlDataDefinitionBlock']['metadata']['title'] = add_data['title']

        # once all editing is done, move the asset is an edit.
        # We do this in order to ensure the path and name are correct everytime.
        # We decided to leave this as a move instead of adding checks to see if it does or does not move.
        if e_announcement_id:
            self.move(e_announcement_id, add_data['parentFolderPath'], type='block')

        return e_announcement_data

    # dates are set to readonly if they occur before today
    def set_readonly_values(self, edit_data):
        # print edit_data
        today = datetime.now()
        first_readonly = False
        second_readonly = False
        if edit_data['first_date'] < today:
            first_readonly = edit_data['first_date'].strftime('%A %B %d, %Y')
        if 'second_date' in edit_data and edit_data['second_date'] and edit_data['second_date'] < today:
            second_readonly = edit_data['second_date'].strftime('%A %B %d, %Y')

        edit_data['first_readonly'] = first_readonly
        edit_data['second_readonly'] = second_readonly

    def get_e_announcement_parent_folder(self, date):
        # break the date into Year/month
        split_date = date.split("-")
        month = self.convert_month_num_to_name(split_date[0])
        year = split_date[2]
        
        # the copy method only processes if the folder being copied does not exist already.
        self.copy(app.config['BASE_ASSET_BASIC_FOLDER'], '/e-announcements/' + year, 'folder')
        self.copy(app.config['BASE_ASSET_BASIC_FOLDER'], '/e-announcements/' + year + "/" + month, 'folder')

        return "/e-announcements/" + year + "/" + month

    # this callback is used with the /edit_all endpoint. The primary use is to modify all assets
    def edit_all_callback(self, asset_data):
        pass

    def split_user_e_annz(self, forms):
        user_forms = []
        other_forms = []
        for form in forms:
            if form['author'] is not None and session['username'] in form['author']:
                user_forms.append(form)
            else:
                other_forms.append(form)
        return user_forms, other_forms

    def get_search_results(self, selection, title, date):
        announcements = self.traverse_xml(app.config['E_ANNOUNCEMENTS_XML_URL'], 'system-block')
        if selection and '-'.join(selection) == '2':
            e_annz_to_iterate = announcements
            forms_header = "All E-Announcements"
        else:
            user_e_annz, other_e_annz = self.split_user_e_annz(announcements)
            if selection and '-'.join(selection) == '1':
                e_annz_to_iterate = user_e_annz
                forms_header = "My E-Announcements"
            else:
                e_annz_to_iterate = other_e_annz
                forms_header = "Other E-Announcements"
        # Early return if no parameters to check in the search
        if not title and not date:
            return e_annz_to_iterate, forms_header

        # to_return will hold all of the events that match the search criteria
        to_return = []

        both = title and date
        for annz in e_annz_to_iterate:
            title_matches = title and title.lower() in annz['title'].lower()
            format_first_date = datetime.strptime(annz['first_date'], "%A %B %d, %Y")
            format_second_date = None
            if annz['second_date']:
                format_second_date = datetime.strptime(annz['second_date'], "%A %B %d, %Y")
            date_matches = date and (date == format_first_date or date == format_second_date)

            # If title and date matches, add the announcement
            if title_matches and date_matches:
                to_return.append(annz)

            # If title or date matches, add the announcement
            if not both and (title_matches or date_matches):
                to_return.append(annz)

        return to_return, forms_header

    def get_title_and_message(self, form, ea_display):
        title = find(form, 'title', False)
        message = find(form, 'message', False)
        ea_id = find(form, 'id', False)
        created = find(form, 'created-on', False)
        ea_display.append({
            'title': title,
            'message': message,
            'id': ea_id
        })

    @cache.memoize(timeout=600)
    def get_upcoming(self, forms, date_id, ea_display):
        for form in forms:
            first_ea_date = find(form, 'first_date', False)

            if first_ea_date == str(date_id):
                self.get_title_and_message(form, ea_display)

            # second date is not always present, the second date if statements are necessary
            second_ea_date = find(form, 'second_date', False)
            if second_ea_date != '':
                if second_ea_date == str(date_id):
                    self.get_title_and_message(form, ea_display)
        return ea_display

    def is_bethel_holiday(self, date):
        # New years
        if date.month == 1 and date.day == 1:
            return True
        # New Years(observed) -- If new years day is on the weekend, we get the monday off (2nd or 3rd)
        elif date.month == 1 and date.weekday() == 0 and (date.day == 2 or date.day == 3):
            return True
        # MLK Day - 3rd monday in jan
        elif date.month == 1 and date.weekday() == 0 and math.ceil(date.day/7.0) == 3:
            return True
        # Easter (is the date the friday before easter)
        elif self.is_date_friday_before_easter(date):
            return True
        # memorial day - last monday in may (may, date is after 24th and its a monday)
        elif date.month == 5 and date.day > 24 and date.weekday() == 0:
            return True
        # july 4
        elif date.month == 7 and date.day == 4:
            return True
        # Labor Day - first monday in sept
        elif date.month == 9 and date.weekday() == 0 and math.ceil(date.day/7.0) == 1:
            return True
        # Black Friday -- the friday after the fourth thursday in nov
        elif date.month == 11 and math.ceil((date.day-1)/7.0) == 4 and date.weekday() == 4:
            return True
        # Christmas Eve(observed) - christmas eve is on the weekend, we get the friday off (22nd or 23rd).
        elif date.month == 12 and date.weekday() == 4 and (date.day == 22 or date.day == 23):
            return True
        # christmas days
        elif date.month == 12 and date.day >= 24:
            return True

        return False

    def is_date_friday_before_easter(self, date):
        year = date.year

        # code from http://code.activestate.com/recipes/576517-calculate-easter-western-given-a-year/
        a = year % 19
        b = year // 100
        c = year % 100
        d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
        e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
        f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
        month = f // 31
        day = f % 31 + 1

        return date.month == month and date.day == (day - 2)
