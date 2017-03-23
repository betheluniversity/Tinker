import datetime
from createsend import *
from bu_cascade.asset_tools import find

# tinker
from tinker import app
from tinker.tinker_controller import requires_auth

# news controller
from campaign_controller import NewsController

# flask
from flask import Blueprint, render_template, url_for, redirect, session
from flask_classy import FlaskView, route, request

NewsBlueprint = Blueprint('news', __name__, template_folder='templates')


class NewsView(FlaskView):
    route_base = '/news'

    def __init__(self):
        self.base_campaign = NewsController()

    def before_request(self, name, **kwargs):
        pass

    # todo: make sure apache configs are good to go
    # todo: activate auth for prod
    # @requires_auth
    @route('/api/send-email/<article_id>', methods=['get', 'post'])
    def reset_send_email(self, article_id):
        try:
            resp = None
            page = self.base_campaign.read_page(article_id)
            article_asset, md, sd = page.get_asset()

            news_article_datetime = datetime.datetime.fromtimestamp(int(find(sd, 'publish-date', False))/1000)
            current_datetime = datetime.datetime.now()

            # todo: update for prod
            # if news_article_datetime.strftime("%m-%d-%Y") != current_datetime.strftime("%m-%d-%Y"):
            #     return None

            # add news_article
            news_article_text = self.base_campaign.create_single_news_article(article_asset, news_article_datetime)
            news_article_title = find(md, 'title', False)

            if news_article_text != '':
                campaign_monitor_key = app.config['NEWS_CAMPAIGN_MONITOR_KEY']
                CreateSend({'api_key': campaign_monitor_key})
                new_campaign = Campaign({'api_key': campaign_monitor_key})

                client_id = app.config['NEWS_CLIENT_ID']
                subject = news_article_title + ' | Bethel News'
                name = '%s | %s' % (news_article_title, str(current_datetime.strftime('%m/%-d/%Y')))
                from_name = 'Bethel News'
                from_email = 'news@bethel.edu'
                reply_to = 'news@bethel.edu'
                list_ids = [app.config['NEWS_LIST_KEY']]
                segment_ids = [app.config['NEWS_SEGMENT_ID']]
                template_id = app.config['NEWS_TEMPLATE_ID']
                template_content = {
                    "Singlelines": [
                        {
                            "Content": news_article_text
                        }
                    ]
                }

                # todo: update for prod
                if app.config['ENVIRON'] == 'prod' or True:
                    self.base_campaign.log_sentry(
                        "News was sent out for id:" + article_id + " was called on production", current_datetime.strftime("%m-%d-%Y"))
                    self.base_campaign.reset_send_email_value(page)

                    # # Todo: someday ---- if a campaign already exists, delete the old one and create a new one
                    resp = new_campaign.create_from_template(client_id, subject, name, from_name, from_email, reply_to,
                                                             list_ids,
                                                             segment_ids, template_id, template_content)
                    #
                    # if 'create_and_send_campaign' in request.url_rule.rule and app.config['ENVIRON'] == 'prod':
                    #     # Send the news out to ALL users at 5:30 am.
                    #     confirmation_email_sent_to = ', '.join(app.config['ADMINS'])
                    #     new_campaign.send(confirmation_email_sent_to, str(date.strftime('%Y-%m-%d')) + ' 05:30')
                    #     self.base_campaign.log_sentry("News campaign was sent", resp)

        except:
            return None

        return resp


NewsView.register(NewsBlueprint)
