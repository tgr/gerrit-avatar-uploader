# -*- coding: utf-8 -*-

import hashlib
import json
import ldap
import requests
from typing import Dict, Optional, Union
import urllib.parse


class ErrorMessageException(Exception):
    pass


def get_ldap_email(username: str, base_url: str) -> Dict:
    with ldap.initialize(base_url) as conn:
        member_dn = 'uid={},ou=people,dc=wikimedia,dc=org'.format(username)
        try:
            data = conn.search_s(member_dn, ldap.SCOPE_BASE)
            # fullname = ldap_info['cn'][0].decode()
            return data['mail'][0].decode()
        except ldap.NO_SUCH_OBJECT:
            raise ErrorMessageException('User account not found')


def get_gerrit_email(username: str, base_url: str) -> str:
    url_params = {'username': username}
    return gerrit_api_query(base_url, 'GET', '/accounts/{username}', url_params=url_params)['email']


def get_gerrit_avatar(username: str, base_url: str) -> Optional[str]:
    url_params = {'username': username}
    r = gerrit_api_query(base_url, 'GET', '/accounts/{username}/avatar', url_params=url_params)
    if r.status_code == requests.codes.found:
        return r.headers['Location']
    else:
        return None


def gerrit_api_query(
    base_url: str,
    verb: str,
    endpoint: str,
    params: Dict = None,
    url_params: Dict = None,
    raw_response: bool = False
) -> Union[Dict, requests.Response]:
    if base_url.endswith('/') and endpoint.startswith('/'):
        endpoint = endpoint[1:]
    if url_params:
        url_params = {k: urllib.parse.quote(v, '') for k, v in url_params.items()}
        endpoint = endpoint.format(**url_params)

    if verb == 'GET':
        r = requests.get(base_url + endpoint, params=params)
    elif verb == 'POST':
        r = requests.post(base_url + endpoint, data=params)
    else:
        raise ErrorMessageException('Internal error: invalid verb ' + verb)

    if raw_response:
        return r

    if r.status_code != requests.codes.ok:
        raise ErrorMessageException('Gerrit request for %s %s failed: %s %s'
                                    % (verb, endpoint, r.status_code, r.reason))

    text = r.text.split('\n', 1)[1]  # remove anti-CSRF header
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ErrorMessageException('Could not decode Gerrit response for %s %s: %s' % (verb, endpoint, str(e)))

    return data


def get_gravatar_url(email: str) -> Optional[str]:
    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(email.lower()).hexdigest()
    gravatar_url += '?' + urllib.parse.urlencode({'s': '100'})
    r = requests.head(gravatar_url, allow_redirects = True)
    if r.ok:
        if r.history:
            r = r.history[-1]
        return r.url
    else:
        return None
