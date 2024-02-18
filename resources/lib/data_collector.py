# -*- coding: utf-8 -*-

from urllib.parse import unquote
from difflib import SequenceMatcher

import xbmc
import xbmcaddon

from resources.lib.utilities import log, normalize_string

__addon__ = xbmcaddon.Addon()


def get_file_path():
    return xbmc.Player().getPlayingFile()


def get_media_data(tvshow_workaround = True, original_filename = True):
    item = {"query": None,
            "year": xbmc.getInfoLabel("VideoPlayer.Year") if xbmc.getInfoLabel(u"VideoPlayer.Year") else '',
            "season_number": str(xbmc.getInfoLabel("VideoPlayer.Season")) if xbmc.getInfoLabel(u"VideoPlayer.Season") else '',
            "episode_number": str(xbmc.getInfoLabel("VideoPlayer.Episode")) if xbmc.getInfoLabel(u"VideoPlayer.Episode") else '',
            "title": normalize_string(xbmc.getInfoLabel("VideoPlayer.title")) if xbmc.getInfoLabel("VideoPlayer.title") else '',
            "tv_show_title": normalize_string(xbmc.getInfoLabel("VideoPlayer.TVshowtitle")) if xbmc.getInfoLabel(u"VideoPlayer.TVshowtitle") else None,
            "original_title": normalize_string(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")) if xbmc.getInfoLabel(u"VideoPlayer.OriginalTitle") else None}

    if item["tv_show_title"]:
        item["query"] = item["tv_show_title"]
        
        # WORKAROUND FOR TV SHOWS DUE TO NONFUNCTIONAL EPISODE AND SEASON PARAMS IN API
        if tvshow_workaround == 'true':
            if item["season_number"] and item["episode_number"]:
                item["query"] = "{0}+S{1:0>2}E{2:0>2}".format(item["query"], item["season_number"], item["episode_number"])
                item["season_number"] = ''
                item["episode_number"] = ''

        item["year"] = None  # Kodi gives episode year, OS searches by series year. Without year safer.
        item["imdb_id"] = None  # Kodi gives strange id. Without id safer.

        # TODO if no season and episode numbers use guessit
        
        # WORKAROUND TO NOT USE INTERNACIONALIZED TV Show Name, there is no Originatl tv show title
        if original_filename == 'true':
            item[u"query"] = None     # search() will replace query with basename

    elif item["original_title"]:
        item["query"] = item["original_title"]

        if not item["query"]:
            log(__name__, "query still blank, fallback to VideoPlayer.title")
            item["query"] = normalize_string(xbmc.getInfoLabel("VideoPlayer.Title")) if xbmc.getInfoLabel("VideoPlayer.title") else '' # no original title, get just Title
            # TODO try guessit if no proper title here

    # TODO get episodes like that and test them properly out
    #if item["episode_number"].lower().find("s") > -1:  # Check if season is "Special"
    #    item["season_number"] = "0"  #
    #    item["episode_number"] = item["episode_number"][-1:]

    return item


def get_language_data(params):
    search_languages = unquote(params.get("languages")).split(",")
    preferred_language = params.get("preferredlanguage")

    # fallback_language = __addon__.getSetting("fallback_language")

    if preferred_language and preferred_language not in search_languages and preferred_language != "Unknown"  and preferred_language != "Undetermined": 
        search_languages.append(preferred_language)

    """ should implement properly as fallback, not additional language, leave it for now
    """
    
    #if fallback_language and fallback_language not in search_languages:
    #    search_languages_str=search_languages_str+","+fallback_language

        #search_languages_str=fallback_language

    sanitized_languages = []
    for language in search_languages:
        lang = convert_language(language)
        if lang:
            sanitized_languages.append(lang)
        #item["languages"].append(lang)
            #if search_languages_str=="":
            #    search_languages_str=lang                            
           # if lang=="Undetermined":
            #    search_languages_str=search_languages_str
            #else:    
            
        else:
            log(__name__, f"Language code not found: '{language}'")

    if sanitized_languages:
        search_languages_str = ",".join(sorted(sanitized_languages))
    else:
        # fallback if sanitization failed
        search_languages_str = ",".join(sorted(search_languages))
    
    item = {
        "hearing_impaired": __addon__.getSetting("hearing_impaired"),
        "foreign_parts_only": __addon__.getSetting("foreign_parts_only"),
        "machine_translated": __addon__.getSetting("machine_translated"),
        "languages": search_languages_str}

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
        "English": "en",
        "Portuguese (Brazil)": "pt-br",
        "Portuguese": "pt-pt",
        "Chinese (simplified)": "zh-cn",
        "Chinese (traditional)": "zh-tw"}
    reverse_language_list = {v: k for k, v in list(language_list.items())}

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


def clean_feature_release_name(title, release, movie_name=""):
    if not title:
        if not movie_name:
            if not release:
                raise ValueError("None of title, release, movie_name contains a string")
            return release
        else:
            if not movie_name[0:4].isnumeric():
                name = movie_name
            else:
                name = movie_name[7:]
    else:
        name = title

    match_ratio = SequenceMatcher(None, name, release).ratio()
    #log(__name__, f"name: {name}, release: {release}, match_ratio: {match_ratio}")
    if name in release:
        return release
    elif match_ratio > 0.3:
        return release
    else:
        return f"{name} {release}"
