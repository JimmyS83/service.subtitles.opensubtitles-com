# -*- coding: utf-8 -*-

from __future__ import absolute_import
from urllib import unquote
from difflib import SequenceMatcher

import xbmc
import xbmcaddon

from resources.lib.utilities import log, normalize_string

from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon()


def get_file_path():
    return xbmc.Player().getPlayingFile()


def get_media_data(tvshow_workaround = False):
    item = {u"year": int(xbmc.getInfoLabel(u"VideoPlayer.Year")) if xbmc.getInfoLabel(u"VideoPlayer.Year") else u'',
            u"season_number": int(xbmc.getInfoLabel(u"VideoPlayer.Season")) if xbmc.getInfoLabel(u"VideoPlayer.Season") else u'',
            u"episode_number": int(xbmc.getInfoLabel(u"VideoPlayer.Episode")) if xbmc.getInfoLabel(u"VideoPlayer.Episode") else u'',
            u"title": normalize_string(xbmc.getInfoLabel(u"VideoPlayer.title")) if xbmc.getInfoLabel(u"VideoPlayer.title") else u'',
            u"tv_show_title": normalize_string(xbmc.getInfoLabel(u"VideoPlayer.TVshowtitle")) if xbmc.getInfoLabel(u"VideoPlayer.TVshowtitle") else u'',
            u"original_title": normalize_string(xbmc.getInfoLabel(u"VideoPlayer.OriginalTitle")) if xbmc.getInfoLabel(u"VideoPlayer.OriginalTitle") else u''}

    if item[u"tv_show_title"]:
        item[u"query"] = item[u"tv_show_title"]

        # WORKAROUND FOR TV SHOWS DUE TO NONFUNCTIONAL EPISODE AND SEASON PARAMS IN API
        if tvshow_workaround == 'true':
            if item[u"season_number"] and item[u"episode_number"]:
                item[u"query"] = "{0}+S{1:0>2}E{2:0>2}".format(item[u"query"], item[u"season_number"], item[u"episode_number"])
                item[u"season_number"] = ''
                item[u"episode_number"] = ''

        item[u"year"] = None  # Kodi gives episode year, OS searches by series year. Without year safer.
        item[u"imdb_id"] = None  # Kodi gives strange id. Without id safer.
        # TODO if no season and episode numbers use guessit

    elif item[u"original_title"]:
        item[u"query"] = item[u"original_title"]

  #  if not item["query"]:
  #      log(__name__, "VideoPlayer.OriginalTitle not found")
  #      item["query"] = normalize_string(xbmc.getInfoLabel("VideoPlayer.Title"))  # no original title, get just Title
  #      # TODO try guessit if no proper title here

    # TODO get episodes like that and test them properly out
    #if item[u"episode_number"].lower().find(u"s") > -1:  # Check if season is "Special"
    #    item[u"season_number"] = 0  #
    #    item[u"episode_number"] = item[u"episode_number"][-1:]

    return item


def get_language_data(params):
    search_languages = unquote(params.get(u"languages")).split(u",")
    search_languages_str = u""
    preferred_language = params.get(u"preferredlanguage")

    # fallback_language = __addon__.getSetting("fallback_language")
    
    
    log(__name__, u"params '%s' " % params)
    log(__name__, u"search_languages '%s' " % search_languages)

    if preferred_language and preferred_language not in search_languages and preferred_language != u"Unknown"  and preferred_language != u"Undetermined": 
        search_languages.append(preferred_language)
        search_languages_str="{0},{1}".format(search_languages_str, preferred_language)

    u""" should implement properly as fallback, not additional language, leave it for now
    """
    
    #if fallback_language and fallback_language not in search_languages:
    #    search_languages_str=search_languages_str+","+fallback_language

        #search_languages_str=fallback_language
        
    for language in search_languages:
        lang = convert_language(language)
        if lang:
            log(__name__, "Language  found: '{0}' search_languages_str:'{1}".format(lang, search_languages_str))
            if search_languages_str==u"":
                search_languages_str=lang    
            else:
                search_languages_str=search_languages_str+u","+lang
        #item["languages"].append(lang)
            #if search_languages_str=="":
            #    search_languages_str=lang                            
           # if lang=="Undetermined":
            #    search_languages_str=search_languages_str
            #else:    
            
        else:
            log(__name__, "Language code not found: '{}'".format(language))









    
    item = {
        u"hearing_impaired": __addon__.getSetting(u"hearing_impaired"),
        u"foreign_parts_only": __addon__.getSetting(u"foreign_parts_only"),
        u"machine_translated": __addon__.getSetting(u"machine_translated"),
        u"languages": search_languages_str}

     # for language in search_languages:
     #  lang = convert_language(language)

     #  if lang:
     #      #item["languages"].append(lang)
     #      item["languages"]=item["languages"]+","+lang
     #  else:
     #      log(__name__, f"Language code not found: '{language}'")
     
    return item


def convert_language(language, reverse=False):
    language_list = {
        u"English": u"en",
        u"Portuguese (Brazil)": u"pt-br",
        u"Portuguese": u"pt-pt",
        u"Chinese (simplified)": u"zh-cn",
        u"Chinese (traditional)": u"zh-tw"}
    reverse_language_list = dict((v, k) for k, v in list(language_list.items()))

    if reverse:
        iterated_list = reverse_language_list
        xbmc_param = xbmc.ENGLISH_NAME
    else:
        iterated_list = language_list
        xbmc_param = xbmc.ISO_639_1

    if language in iterated_list:
        return iterated_list[language]
    else:
        return xbmc.convertLanguage(language, xbmc_param)


def clean_feature_release_name(title, release, movie_name=u""):
    if not title:
        if not movie_name:
            if not release:
                raise ValueError(u"None of title, release, movie_name contains a string")
            return release
        else:
            if not movie_name[0:4].isnumeric():
                name = movie_name
            else:
                name = movie_name[7:]
    else:
        name = title

    match_ratio = SequenceMatcher(None, name, release).ratio()
    # log(__name__, "name: {0}, release: {1}, match_ratio: {2}".format(name, release, match_ratio))
    if name in release:
        return release
    elif match_ratio > 0.3:
        return release
    else:
        return "{0} {1}".format(name, release)
