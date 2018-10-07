# -*- coding: utf-8 -*-

import flask
#import mwoauth
import yaml
import os
import toolforge
import utils

app = flask.Flask(__name__)
app.before_request(toolforge.redirect_to_https)
toolforge.set_user_agent('gerrit-avatar-uploader')

__dir__ = os.path.dirname(__file__)
with open(os.path.join(__dir__, 'config.yaml')) as config_file:
    app.config.update(yaml.safe_load(config_file))


@app.errorhandler(utils.ErrorMessageException)
def handle_error(e):
    flask.flash(str(e), 'error')
    return flask.render_template('index.html')


@app.route('/')
def index():
    #username = flask.session.get('username', None)
    return flask.render_template('index.html')


@app.route('/lookup/<username>')
def lookup(username):
    emails = []

    # try LDAP email
    emails.append(utils.get_ldap_email(username, app.config['LDAP_BASE_URL']))

    # try Gerrit email
    emails.append(utils.get_gerrit_email(username, app.config['GERRIT_API_BASE_URL']))

    # filter null and duplicates
    emails = list(set(filter(None.__ne__, emails)))

    gravatar_urls = [utils.get_gravatar_url(email) for email in emails]

    # check existing avatar url
    current_avatar_url = utils.get_gerrit_avatar(username, app.config['GERRIT_API_BASE_URL'])

    # TODO merge into index.html
    return flask.render_template('lookup.html', gravatar_urls = gravatar_urls, current_avatar_url = current_avatar_url)

# TODO support selecting non-gravatar sources (Phabricator? Commons? arbitrary URL?)

# TODO route and handling code for actually submitting an image to Gerrit,
# including resizing to the right format

# TODO check if there's a way to get LDAP username from Wikimedia
# username - if so, uncomment the block below so we can verify identity
#
# @app.route('/login')
# def login():
#     """Initiate an OAuth login."""
#     consumer_token = mwoauth.ConsumerToken(
#         app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
#     try:
#         redirect, request_token = mwoauth.initiate(
#             app.config['OAUTH_MWURI'], consumer_token)
#     except Exception as e:
#         app.logger.exception('mwoauth.initiate failed')
#         flask.flash(u'OAuth initiation failed: ' + str(e), 'error')
#         return flask.redirect(flask.url_for('index'))
#     else:
#         flask.session['request_token'] = dict(zip(
#             request_token._fields, request_token))
#         return flask.redirect(redirect)
#
# @app.route('/oauth-callback')
# def oauth_callback():
#     if 'request_token' not in flask.session:
#         flask.flash(u'OAuth callback failed. Are cookies disabled?', 'error')
#         return flask.redirect(flask.url_for('index'))
#
#     consumer_token = mwoauth.ConsumerToken(
#         app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
#
#     try:
#         access_token = mwoauth.complete(
#             app.config['OAUTH_MWURI'],
#             consumer_token,
#             mwoauth.RequestToken(**flask.session['request_token']),
#             flask.request.query_string)
#
#         identity = mwoauth.identify(
#             app.config['OAUTH_MWURI'], consumer_token, access_token)
#     except Exception as e:
#         app.logger.exception('OAuth authentication failed: ' + str(e))
#
#     else:
#         flask.session['access_token'] = dict(zip(
#             access_token._fields, access_token))
#         flask.session['username'] = identity['username']
#
#     return flask.redirect(flask.url_for('index'))
