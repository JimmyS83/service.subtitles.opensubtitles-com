# -*- coding: utf-8 -*-

from __future__ import absolute_import
#from typing import Union

from requests import Session, ConnectionError, HTTPError, ReadTimeout, Timeout, RequestException

from resources.lib.oss.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.oss.model.request.download import OpenSubtitlesDownloadRequest

u'''local kodi module imports. replace by any other exception, cache, log provider'''
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests
from resources.lib.cache import Cache
from resources.lib.utilities import log

API_URL = u"https://api.opensubtitles.com/api/v1/"
API_LOGIN = u"login"
API_SUBTITLES = u"subtitles"
API_DOWNLOAD = u"download"

CONTENT_TYPE = u"application/json"
REQUEST_TIMEOUT = 30

class_lookup = {u"OpenSubtitlesSubtitlesRequest": OpenSubtitlesSubtitlesRequest,
                u"OpenSubtitlesDownloadRequest": OpenSubtitlesDownloadRequest}


# TODO implement search for features, logout, infos, guessit. Response(-s) objects

# Replace with any other log implementation outside fo module/Kodi
def logging(msg):
    return log(__name__, msg)


def query_to_params(query, _type):
    logging(u"type call: {0}".format(_type))
    logging(u"type of query: {0}".format(type(query)))
    logging(u"query: {0}".format(query))
    if type(query) is dict or set:
        try:
            request = class_lookup[_type](**query)
        except ValueError, e:
            raise ValueError("Invalid request data provided: {0}".format(e))
    elif type(query) is _type:
        request = query
    else:
        raise ValueError(u"Invalid request data provided. Invalid query type")

    logging(u"request vars: ")
    logging(vars(request))
    params = request.request_params()
    logging(u"params: ")
    logging(params)
    return params


class OpenSubtitlesProvider(object):

    def __init__(self, api_key, username, password, tvshow_workaround):

       # if not all((username, password)):
       #     raise ConfigurationError("Username and password must be specified")

        if not api_key:
            raise ConfigurationError(u"Api_key must be specified")

        self.api_key = api_key
        self.username = username
        self.password = password
        self.tvshow_workaround = tvshow_workaround

        self.request_headers = {u"Api-Key": self.api_key, u"Content-Type": CONTENT_TYPE, u"Accept": CONTENT_TYPE}

        self.session = Session()
        self.session.headers = self.request_headers

        # Use any other cache outside of module/Kodi
        self.cache = Cache(key_prefix=u"os_com")

    # make login request. Sets auth token
    def login(self):

        # build login request
        login_url = API_URL + API_LOGIN
        login_body = {u"username": self.username, u"password": self.password}

        try:
            r = self.session.post(login_url, json=login_body, allow_redirects=False, timeout=REQUEST_TIMEOUT)
            logging(r.url)
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout), e:
            raise ServiceUnavailable("Unknown Error: status code {0}".format(e.response.status_code))
        except HTTPError, e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError("Login failed: {0}".format(e))
            elif status_code == 429:
                raise TooManyRequests()
            elif status_code == 503:
                raise ProviderError(e)
            else:
                raise ProviderError("Bad status code: {0}".format(status_code))
        else:
            try:
                self.user_token = r.json()[u"token"]
            except ValueError:
                raise ValueError(u"Invalid JSON returned by provider")

    @property
    def user_token(self):
        return self.cache.get(key=u"user_token")

    @user_token.setter
    def user_token(self, value):
        self.cache.set(key=u"user_token", value=value)

    def search_subtitles(self, query):

        params = query_to_params(query, u'OpenSubtitlesSubtitlesRequest')

        if not len(params):
            raise ValueError(u"Invalid subtitle search data provided. Empty Object built")

        try:
            # build query request
            subtitles_url = API_URL + API_SUBTITLES
            r = self.session.get(subtitles_url, params=params, timeout=30)
            logging(r.url)
            logging(r.request.headers)
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout), e:
            raise ServiceUnavailable("Unknown Error, empty response, status code: {0}".format(e.status_code))
        except HTTPError, e:
            status_code = e.response.status_code
            if status_code == 429:
                raise TooManyRequests()
            elif status_code == 503:
                raise ProviderError(e)
            else:
                raise ProviderError("Bad status code: {0}".format(status_code))

        try:
            result = r.json()
            if u"data" not in result:
                raise ValueError
        except ValueError:
            raise ProviderError(u"Invalid JSON returned by provider")
        else:
            logging("Query returned {0} subtitles".format(len(result['data'])))

        if len(result[u"data"]):
            return result[u"data"]

        return None

    def download_subtitle(self, query):
        if self.user_token is None:
            logging(u"No cached token, we'll try to login again.")
            try:
                self.login()
            except AuthenticationError, e:
                logging(u"Unable to authenticate.")
            #    raise AuthenticationError("Unable to authenticate.")
            #except (ServiceUnavailable, TooManyRequests, ProviderError, ValueError) as e:
            #    logging("Unable to obtain an authentication token.")
            #    raise ProviderError(f"Unable to obtain an authentication token: {e}")
        if self.user_token == u"":
            logging(u"Unable to obtain an authentication token.")
            #raise ProviderError("Unable to obtain an authentication token")
        
            
        
        logging("user token is {0}".format(self.user_token))

        params = query_to_params(query, u"OpenSubtitlesDownloadRequest")

        logging("Downloading subtitle {0} ".format(params['file_id']))

        # build download request
        download_url = API_URL + API_DOWNLOAD
        download_headers= {}
        if not self.user_token==None:
            download_headers = {u"Authorization": u"Bearer " + self.user_token}

        download_params = {u"file_id": params[u"file_id"], u"sub_format": u"srt"}

        try:
            r = self.session.post(download_url, headers=download_headers, json=download_params, timeout=REQUEST_TIMEOUT)
            logging(r.url)
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout), e:
            raise ServiceUnavailable("Unknown Error, status code: {0}".format(e.status_code))
        except HTTPError, e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError("Login failed: {0}".format(e.response.reason))
            elif status_code == 429:
                raise TooManyRequests()
            elif status_code == 406:
                raise DownloadLimitExceeded("Daily download limit reached: {0}".format(e.response.reason))
            elif status_code == 503:
                raise ProviderError(e)
            else:
                raise ProviderError("Bad status code: {0}".format(status_code))

        try:
            subtitle = r.json()
            download_link = subtitle[u"link"]
        except ValueError:
            raise ProviderError(u"Invalid JSON returned by provider")
        else:
            res = self.session.get(download_link, timeout=REQUEST_TIMEOUT)

            subtitle[u"content"] = res.content

            if not subtitle[u"content"]:
                logging("Could not download subtitle from {0}".format(subtitle.download_link))

        return subtitle
