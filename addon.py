# -*- coding: utf8 -*-
import json
import xbmcaddon
import xbmcgui
import xbmcplugin
import os
import sys
import urllib2
import urllib
import xbmc
import re
from utils import get_params, getRemoteData, remoteFileExists


API_URL = "http://api.seasonvar.ru/"
PREFIX = "/video/seasonvarserials"


PLUGIN_HANDLE = int(sys.argv[1])
####################################################################################################
# Start and main menu
####################################################################################################
ADDON = xbmcaddon.Addon(id='plugin.video.seasonvar.ru.standalone')
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
API_KEY = ADDON.getSetting('API_KEY')
USE_HD = ADDON.getSetting('USE_HD')
IS_DEBUG = ADDON.getSetting('IS_DEBUG')
STRING = ADDON.getLocalizedString

def LOG(message):
    if IS_DEBUG == 'true':
        xbmc.log('Seasonvar.ru.standalone: '+str(message))

def showDialogBox(message):
    xbmcgui.Dialog().ok('message',message)

def SelectFromEnglishNames():
    items = []
    if is_key_active():

        abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
               'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z']

        for letter in abc:

            item = xbmcgui.ListItem(letter)
            sys_url = sys.argv[0] + '?mode=get_serial_list_by_title&letter='+letter
            itemData = (sys_url,item, True)
            items.append(itemData)
    else:
        display_missing_key_message()
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def SelectFromRussianNames():
    items = []
    if is_key_active():

        abc = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Э', 'Ю', 'Я']

        for letter in abc:

            item = xbmcgui.ListItem(letter)
            sys_url = sys.argv[0] + '?mode=get_serial_list_by_title&letter='+letter
            itemData = (sys_url,item, True)
            items.append(itemData)
    else:
        display_missing_key_message()
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def MainMenu():
    item = xbmcgui.ListItem(STRING(30100))
    sys_url = sys.argv[0] + '?mode=select_from_russian_names'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys_url, item, True)

    item = xbmcgui.ListItem(STRING(30101))
    sys_url = sys.argv[0] + '?mode=select_from_english_names'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys_url, item, True)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


######################################################################################
# List serial by selected letter
######################################################################################


def get_serial_list_by_title(title):
    if is_key_active():
        values = {'key': API_KEY, 'command': 'getSerialList', 'letter': urllib.unquote(title)}

        # do http request for search data
        response = getRemoteData(API_URL, values)
        response = json.loads(response)
        if is_authorized(response):

            if isinstance(response, dict) and 'error' in response.values():
                showDialogBox(
                    STRING(30108)
                )
            else:
                for serial in response:
                    total = serial.get('count_of_seasons')
                    serial_title = serial.get('name')
                    serial_thumb = serial.get('poster')
                    serial_summary = serial.get('description')
                    serial_country = serial.get('country')
                    if total:
                        item = xbmcgui.ListItem(serial_title+' ['+STRING(30102)+': '+total+']')
                        item.setIconImage(serial_thumb)
                        sys_url = sys.argv[0] + '?mode=get_season_list_by_title&title='+serial_title
                        xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys_url, item, True)

                    else:
                        # there are no seasons
                        item = xbmcgui.ListItem(serial_title)
                        item.setIconImage(serial_thumb)
                        sys_url = sys.argv[0] + '?mode=get_season_by_id&id='+serial.get('last_season_id')
                        xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys_url, item, True)
        else:
            return display_unauthorized_message()
    else:
        return display_missing_key_message()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def get_season_list_by_title(title):
    if is_key_active():
        values = {
            'command': 'getSeasonList',
            'name': urllib.unquote(title),
            'key': API_KEY
        }

        response = getRemoteData(API_URL, values)
        response = json.loads(response)

        if is_authorized(response):

            if isinstance(response, dict) and 'error' in response.values():
                showDialogBox(
                    STRING(30108)
                )
            else:
                items = []
                for season in response:
                    season_id = season.get('id')
                    season_number = season.get('season_number')
                    item = xbmcgui.ListItem(season.get('name')+' '+STRING(30103)+' '+season_number)
                    item.setIconImage(season.get('poster'))
                    sys_url = sys.argv[0] + '?mode=get_season_by_id&id='+season_id
                    itemData = (sys_url, item, True)
                    items.append(itemData)

                xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)

        else:
            return display_unauthorized_message()
    else:
        return display_missing_key_message()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def get_season_by_id(id):
    if is_key_active():
        values = {
            'command': 'getSeason',
            'season_id': id,
            'key': API_KEY
        }

        response = getRemoteData(API_URL, values)
        response = json.loads(response)

        if is_authorized(response):

            playlist = response.get('playlist')
            items = []
            for video in playlist:
                video_name = video.get('name')
                try:
                    perevod = video.get('perevod')
                    video_name = video_name + ' ['+STRING(30104)+': '+perevod+']'
                except:
                    pass
                video_link = video.get('link')
                item = xbmcgui.ListItem(video_name)
                item.setProperty('IsPlayable', 'true')
                LOG('video link from json '+video_link)
                try:
                    if USE_HD == 'true':
                        LOG('USE_HD is enabled')
                        video_link_hd = video_link.replace('7f_','hd_')
                        video_link_hd = re.sub(r'data[0-9]*\-[a-zA-Z]*\.datalock\.ru','data-hd.datalock.ru',video_link_hd)
                        LOG('video link converted to HD '+video_link_hd)
                        if remoteFileExists(video_link_hd):
                            video_link = video_link_hd
                except:
                    LOG('Problem in converting video link to HD '+str(sys.exc_info()))
                LOG('result video link for menu '+video_link)
                itemData = (video_link, item, False)
                items.append(itemData)
            xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
        else:
            return display_unauthorized_message()
    else:
        return display_missing_key_message()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def is_key_active():
    if API_KEY != '':
        return True

    return False


def is_authorized(response):
    if 'error' in response:
        if (response.get('error') == 'Authentication::getUser::wrong key'):
            return False
    return True


def display_unauthorized_message():
    xbmcgui.Dialog().ok(STRING(30106), STRING(30105))


def display_missing_key_message():
    xbmcgui.Dialog().ok(STRING(30106), STRING(30107))

params = get_params()
if len(params) == 0:
    MainMenu()
elif params['mode'] == 'select_from_english_names':
    SelectFromEnglishNames()
elif params['mode'] == 'select_from_russian_names':
    SelectFromRussianNames()
elif params['mode'] == 'get_serial_list_by_title':
    get_serial_list_by_title(params['letter'])
elif params['mode'] == 'get_season_list_by_title':
    get_season_list_by_title(params['title'])
elif params['mode'] == 'get_season_by_id':
    get_season_by_id(params['id'])
else:
    MainMenu()