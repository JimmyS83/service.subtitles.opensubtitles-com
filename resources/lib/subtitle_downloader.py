# -*- coding: utf-8 -*-

import os
import shutil
import sys
import uuid

import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmc

from resources.lib.data_collector import get_language_data, get_media_data, get_file_path, convert_language, \
    clean_feature_release_name
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests
from resources.lib.file_operations import get_file_data
from resources.lib.oss.provider import OpenSubtitlesProvider
from resources.lib.utilities import get_params, log, error


__addon__ = xbmcaddon.Addon()
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmc.translatePath(__addon__.getAddonInfo(u"profile"))
__temp__ = xbmc.translatePath(os.path.join(__profile__, u"temp", u""))

if xbmcvfs.exists(__temp__):
    shutil.rmtree(__temp__)
xbmcvfs.mkdirs(__temp__)


class SubtitleDownloader(object):

    def __init__(self):

        self.api_key = __addon__.getSetting(u"APIKey")
        self.username = __addon__.getSetting(u"OSuser")
        self.password = __addon__.getSetting(u"OSpass")
        self.original_filename = __addon__.getSetting(u"original_filename")
        self.tvshow_workaround = __addon__.getSetting(u"tvshow_workaround")
        log(__name__, sys.argv)

        self.sub_format = u"srt"
        self.handle = int(sys.argv[1])
        self.params = get_params()
        self.query = {}
        self.subtitles = {}
        self.file = {}

        try:
            self.open_subtitles = OpenSubtitlesProvider(self.api_key, self.username, self.password, self.tvshow_workaround)
        except ConfigurationError:
            error(__name__, 32002, "ConfigurationError")

    def handle_action(self):
        log(__name__, u"action '%s' called" % self.params[u"action"])
        if self.params[u"action"] == u"manualsearch":
            self.search(self.params[u'searchstring'])
        elif self.params[u"action"] == u"search":
            self.search()
        elif self.params[u"action"] == u"download":
            self.download()

    def search(self, query=u""):
        file_data = get_file_data(get_file_path())
        language_data = get_language_data(self.params)

        log(__name__, u"file_data '%s' " % file_data)
        log(__name__, u"language_data '%s' " % language_data)

        # if there's query passed we use it, don't try to pull media data from VideoPlayer
        if query:
            media_data = {u"query": query}
        else:
            media_data = get_media_data(self.tvshow_workaround, self.original_filename)       
            if u"query" not in media_data or not media_data[u"query"]:
                if u"basename" in file_data:
                    media_data[u"query"] = file_data[u"basename"]   # rewrites Original name with basename in query !!!
            log(__name__, u"media_data '%s' " % media_data)

        #self.query = {**media_data, **file_data, **language_data}
        temp_dict = media_data.copy()
        temp_dict.update(file_data)
        temp_dict.update(language_data)
        self.query = temp_dict

        try:
            self.subtitles = self.open_subtitles.search_subtitles(self.query)
        # TODO handle errors individually. Get clear error messages to the user
        except (TooManyRequests, ServiceUnavailable, ProviderError, ValueError):
            error(__name__, 32001, "TooManyRequests, ServiceUnavailable, ProviderError, ValueError")

        if self.subtitles and len(self.subtitles):
            log(__name__, len(self.subtitles))
            #newlist = sorted(self.subtitles, key=lambda d: d['attributes']['language'])
            preffered_language=language_data[u'languages'].split(",");    #  preffered language for list sorting
            newlist = sorted(self.subtitles, key=lambda d: (d['attributes']['language']!=preffered_language, d['attributes']['language'])) 
            self.subtitles = newlist
            
            self.list_subtitles()
        else:
            # TODO retry using guessit???
            log(__name__, u"No subtitle found")
            # TRY with basename
            if u"basename" in file_data:
                log(__name__, u"Trying with basename") 
                media_data[u"query"] = file_data[u"basename"]
                
                temp_dict = media_data.copy()
                temp_dict.update(file_data)
                temp_dict.update(language_data)
                self.query = temp_dict

                try:
                    self.subtitles = self.open_subtitles.search_subtitles(self.query)
                # TODO handle errors individually. Get clear error messages to the user
                except (TooManyRequests, ServiceUnavailable, ProviderError, ValueError):
                    error(__name__, 32001, "TooManyRequests, ServiceUnavailable, ProviderError, ValueError")

                if self.subtitles and len(self.subtitles):
                    log(__name__, len(self.subtitles))
                    #newlist = sorted(self.subtitles, key=lambda d: d['attributes']['language'])
                    preffered_language=language_data[u'languages'].split(",");    #  preffered language for list sorting
                    newlist = sorted(self.subtitles, key=lambda d: (d['attributes']['language']!=preffered_language, d['attributes']['language'])) 
                    self.subtitles = newlist
                    
                    self.list_subtitles()
                else:
                    # TODO retry using guessit???
                    log(__name__, u"No subtitle found")

    def download(self):
        valid = 1
        try:
            self.file = self.open_subtitles.download_subtitle(
                {u"file_id": self.params[u"id"], u"sub_format": self.sub_format})
        # TODO handle errors individually. Get clear error messages to the user
            log(__name__, u"XYXYXX download '%s' " % self.file)
        except AuthenticationError:
            error(__name__, 32003, "AuthenticationError")
            valid = 0
        except DownloadLimitExceeded:
            log(__name__, "XYXYXX limit excedded, username: {0}".format(self.username))
            if self.username==u"":
                error(__name__, 32006, "Empty username")
            else:
                error(__name__, 32004, "DownloadLimitExceeded")
            valid = 0
        except (TooManyRequests, ServiceUnavailable, ProviderError, ValueError):
            error(__name__, 32001, "TooManyRequests, ServiceUnavailable, ProviderError, ValueError")
            valid = 0

        subtitle_path = os.path.join(__temp__, "{0}.{1}".format(str(uuid.uuid4()), self.sub_format))
       
        if (valid==1):
            tmp_file = open(subtitle_path, u"w" + u"b")
            tmp_file.write(self.file[u"content"])
            tmp_file.close()
        

        list_item = xbmcgui.ListItem(label=subtitle_path)
        xbmcplugin.addDirectoryItem(handle=self.handle, url=subtitle_path, listitem=list_item, isFolder=False)

        return

        u"""old code"""
        # subs = Download(params["ID"], params["link"], params["format"])
        # for sub in subs:
        #    listitem = xbmcgui.ListItem(label=sub)
        #    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

    def list_subtitles(self):
        u"""TODO rewrite using new data. do not forget Series/Episodes"""
        x = 0
        for subtitle in reversed(sorted(self.subtitles, key=lambda z: (
                bool(z["attributes"].get("from_trusted", False)),
                z["attributes"].get("votes", 0) or 0,
                z["attributes"].get("ratings", 0) or 0,
                z["attributes"].get("download_count", 0) or 0))):
            x += 1
            if x > 70:
                return
            attributes = subtitle[u"attributes"]
            language = convert_language(attributes[u"language"], True)
            #log(__name__, attributes)
            clean_name = clean_feature_release_name(attributes[u"feature_details"][u"title"], attributes[u"release"],
                                                    attributes[u"feature_details"][u"movie_name"])
            list_item = xbmcgui.ListItem(label=language,
                                         label2=clean_name)
            list_item.setArt({
                u"icon": unicode(int(round(float(attributes[u"ratings"]) / 2))),
                u"thumb": attributes[u"language"]})
            list_item.setProperty(u"sync", u"true" if (u"moviehash_match" in attributes and attributes[u"moviehash_match"]) else u"false")
            list_item.setProperty(u"hearing_imp", u"true" if attributes[u"hearing_impaired"] else u"false")
            u"""TODO take care of multiple cds id&id or something"""
            url = "plugin://{0}/?action=download&id={1}".format(__scriptid__, attributes['files'][0]['file_id'])

            xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)
        xbmcplugin.endOfDirectory(self.handle)
