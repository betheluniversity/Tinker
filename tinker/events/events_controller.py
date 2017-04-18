import json
import datetime
import time
import re
import arrow

# bu-cascade
from bu_cascade.asset_tools import find

# local
from tinker import app
from tinker.tinker_controller import TinkerController

# flask
from flask import render_template, session
from flask import json as fjson


class EventsController(TinkerController):

    # find_all is currently unused for events (but used for the e-annz)
    def inspect_child(self, child, find_all=False):
        try:
            author = child.find('author').text
            author = author.replace(' ', '').split(',')
        except AttributeError:
            author = None
        username = session['username']

        sem_event = False
        post_trad_event = False
        undergrad_event = False
        if 'Tinker Events - CAS' in session['groups']:
            depts = self.search_for_key_in_dynamic_md(child, 'cas-departments')
            undergrad_event = getattr(depts, 'text', None)

        school_event = undergrad_event or post_trad_event or sem_event

        if (author is not None and username in author) or 'Event Approver' in session['groups'] or (school_event and school_event != 'None'):
            try:
                return self._iterate_child_xml(child, author)
            except AttributeError:
                # not a valid event page
                return None
        else:
            return None

    def split_user_events(self, forms):
        username = session['username']
        user_forms = []
        other_forms = []
        for form in forms:
            if form['author'] == username:
                user_forms.append(form)
            else:
                other_forms.append(form)
        return user_forms, other_forms

    def check_new_year_folder(self, event_id, add_data, username):
        current_year = self.get_current_year_folder(event_id)
        new_year = self.get_year_folder_value(add_data)
        if new_year > current_year:
            new_path = self.get_event_folder_path(add_data)
            response = self.move(event_id, new_path[1])
            app.logger.debug(time.strftime("%c") + ": Event move submission by " + username + " " + str(response))

    def _iterate_child_xml(self, child, author):

        roles = []
        values = child.find('dynamic-metadata')
        for value in values:
            if value.tag == 'value':
                roles.append(value.text)

        try:
            is_published = child.find('last-published-on').text
        except AttributeError:
            is_published = False

        dates = child.find('system-data-structure').findall('event-dates')
        dates_str = []
        for date in dates:
            try:
                start = int(date.find('start-date').text) / 1000
                end = int(date.find('end-date').text) / 1000
            except TypeError:
                continue
            dates_str.append(self.friendly_date_range(start, end))

        page_values = {
            'author': author,
            'id': child.attrib['id'] or None,
            'title': child.find('title').text or None,
            'created-on': child.find('created-on').text or None,
            'path': 'https://www.bethel.edu' + child.find('path').text or None,
            'is_published': is_published,
            'event-dates': "<br/>".join(dates_str),
        }
        # This is a match, add it to array

        return page_values

    def get_event_dates(self, form):
        event_dates = []

        num_dates = int(form['num_dates'])
        for i in range(1, num_dates+1):  # the page doesn't use 0-based indexing

            i = str(i)
            new_date = {
                'start-date': form.get('start' + i, ''),
                'end-date': form.get('end' + i, ''),
                'all-day': form.get('allday' + i, ''),
                'need-time-zone': form.get('needtimezone' + i, ''),
                'time-zone': form.get('timezone' + i, '')
            }

            if not new_date['end-date']:
                new_date['end-date'] = form.get('start' + i, '')

            event_dates.append(new_date)

        # convert event dates to JSON
        return event_dates, num_dates

    def check_event_dates(self, num_dates, event_dates):
        dates_good = False
        for i in range(0, num_dates):
            start_and_end = event_dates[i]['start-date'] and event_dates[i]['end-date']

            condition = True
            if event_dates[i]['need-time-zone'] and str(event_dates[i]['time-zone']) == '':
                condition = False

            if start_and_end and condition:
                dates_good = True

        for i in range(0, num_dates):
            try:
                # Get rid of the fancy formatting so we just have normal numbers
                event_dates[i]['start-date'] = event_dates[i]['start-date'].replace('th', '').replace('st', '').replace('rd', '').replace('nd', '')
                event_dates[i]['end-date'] = event_dates[i]['end-date'].replace('th', '').replace('st', '').replace('rd', '').replace('nd', '')

                # Convert to a unix timestamp, and then multiply by 1000 because Cascade uses Java dates
                # which use milliseconds instead of seconds
                try:
                    event_dates[i]['start-date'] = self.date_str_to_timestamp(event_dates[i]['start-date'])
                except ValueError as e:
                    app.logger.error(time.strftime("%c") + ": error converting start date " + str(e))
                    event_dates[i]['start-date'] = None
                try:
                    event_dates[i]['end-date'] = self.date_str_to_timestamp(event_dates[i]['end-date'])
                except ValueError as e:
                    app.logger.error(time.strftime("%c") + ": error converting end date " + str(e))
                    event_dates[i]['end-date'] = None

                if event_dates[i]['all-day']:
                    event_dates[i]['all-day'] = 'Yes'
                else:
                    event_dates[i]['all-day'] = 'No'
                if event_dates[i]['need-time-zone']:
                    event_dates[i]['need-time-zone'] = 'Yes'
                else:
                    event_dates[i]['need-time-zone'] = 'No'

            except KeyError:
                # This will break once we run out of dates
                break

        return json.dumps(event_dates), dates_good

    def validate_form(self, rform, dates_good, dates):

        from forms import EventForm
        form = EventForm()

        if not form.validate_on_submit() or not dates_good:
            if 'event_id' in rform.keys():
                event_id = rform['event_id']
            else:
                new_form = True
            author = rform["author"]
            num_dates = int(rform['num_dates'])

            return render_template('event-form.html', **locals())

    def build_edit_form(self, event_id):
        page = self.read_page(event_id)
        multiple = ['event-dates']
        edit_data = self.get_edit_data(page.get_structured_data(), page.get_metadata(), multiple)
        # set dates and return for use in form
        # convert dates to json so we can use Javascript to create custom DateTime fields on the form
        dates = self.sanitize_dates(edit_data['event-dates'])
        dates = fjson.dumps(dates)

        author = edit_data['author']

        return edit_data, dates, author

    def date_str_to_timestamp(self, date):
        try:
            return int(datetime.datetime.strptime(date, '%B %d  %Y, %I:%M %p').strftime("%s")) * 1000
        except TypeError:
            return None

    def timestamp_to_date_str(self, timestamp_date):
        try:
            return datetime.datetime.fromtimestamp(int(timestamp_date) / 1000).strftime('%B %d  %Y, %I:%M %p')
        except TypeError:
            return None

    def friendly_date_range(self, start, end):
        date_format = "%B %d, %Y %I:%M %p"

        start_check = arrow.get(start)
        end_check = arrow.get(end)

        if start_check.year == end_check.year and start_check.month == end_check.month and start_check.day == end_check.day:
            return "%s - %s" % (datetime.datetime.fromtimestamp(int(start)).strftime(date_format),
                                datetime.datetime.fromtimestamp(int(end)).strftime("%I:%M %p"))
        else:
            return "%s - %s" % (datetime.datetime.fromtimestamp(int(start)).strftime(date_format),
                                datetime.datetime.fromtimestamp(int(end)).strftime(date_format))

    def get_event_structure(self, event_data, metadata, structured_data, add_data, username, workflow=None, event_id=None):
        """
         Could this be cleaned up at all?
        """
        new_data = {}
        for key in add_data:
            try:
                new_data[key.replace("_", "-")] = add_data[key]
            except:
                pass

        # put it all into the final asset with the rest of the SOAP structure
        hide_site_nav, parent_folder_path = self.get_event_folder_path(new_data)

        new_data['parentFolderID'] = ''
        new_data['parentFolderPath'] = parent_folder_path

        new_data['hide-site-nav'] = [hide_site_nav]
        new_data['tinker-edits'] = 1

        # allows for multiple authors. If none set, default to username
        if 'author' not in new_data or new_data['author'] == "":
            new_data['author'] = username

        self.update_asset(event_data, new_data)

        self.add_workflow_to_asset(workflow, event_data)

        if event_id:
            new_data['id'] = event_id

        return event_data

    # Returns (content/config path, parent path)
    def get_event_folder_path(self, data):
        # Check to see if this event should go in a specific folder

        def common_elements(list1, list2):
            # helper function to see if two lists share items
            return [element for element in list1 if element in list2]

        # Find the year we want
        max_year = self.get_year_folder_value(data)

        path = "events/%s" % max_year
        hide_site_nav = "Hide"

        if 'general' in data:
            general = data['general']
        else:
            general = []

        if 'offices' in data:
            offices = data['offices']
        else:
            offices = []

        if 'Athletics' in general:
            hide_site_nav = "Hide"
            path = "events/%s/athletics" % max_year

        elif common_elements(['Johnson Gallery', 'Olson Gallery', 'Art Galleries'],  general):
            hide_site_nav = "Do not hide"
            path = "events/arts/galleries/exhibits/%s" % max_year

        elif 'Music Concerts' in general:
            hide_site_nav = "Do not hide"
            path = 'events/arts/music/%s' % max_year

        elif 'Theatre' in general:
            hide_site_nav = "Do not hide"
            path = 'events/arts/theatre/%s' % max_year

        elif any("Chapel" in s for s in general):
            hide_site_nav = "Hide"
            path = 'events/%s/chapel' % max_year

        elif 'Library' in general:
            hide_site_nav = "Hide"
            path = "events/%s/library" % max_year

        elif 'Bethel Student Government' in offices:
            hide_site_nav = "Hide"
            path = "events/%s/bsg" % max_year

        elif any("Admissions" in s for s in offices):
            hide_site_nav = "Hide"
            path = 'events/%s/admissions' % max_year

        self.copy(app.config['BASE_ASSET_EVENT_FOLDER'], path, 'folder')

        return hide_site_nav, path

    def get_current_year_folder(self, event_id):
        # read in te page and find the current year
        page_asset = self.read(event_id, 'page')
        path = find(page_asset, 'path', False)
        # path = asset['asset']['page']['path']
        try:
            year = re.search('events/(\d{4})/', path).group(1)
            return int(year)
        except AttributeError:
            return None

    def get_year_folder_value(self, data):
        dates = data['event-dates']

        max_year = 0
        for date in dates:
            date_str = self.timestamp_to_date_str(date['end-date'])
            end_date = datetime.datetime.strptime(date_str, '%B %d  %Y, %I:%M %p').date()
            try:
                year = end_date.year
            except AttributeError:
                # if end_date is none and this fails, revert to current year.
                year = datetime.date.today().year
            if year > max_year:
                max_year = year

        return max_year

    # Converts date dict to the date picker format that front-end tinker can read
    def sanitize_dates(self, dates):
        for date in dates:
            if 'all_day' in date and (date['all_day'] == "::CONTENT-XML-CHECKBOX::No" or date['all_day'] == "::CONTENT-XML-CHECKBOX::"):
                date['all_day'] = None
            if 'outside_of_minnesota' in date and (date['outside_of_minnesota'] == "::CONTENT-XML-CHECKBOX::No" or date['outside_of_minnesota'] == "::CONTENT-XML-CHECKBOX::"):
                date['outside_of_minnesota'] = None
        return dates

    # this callback is used with the /edit_all endpoint. The primary use is to modify all assets
    def edit_all_callback(self, asset_data):
        pass
