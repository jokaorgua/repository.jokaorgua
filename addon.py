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
PLUGIN_HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.video.seasonvar.ru.standalone')
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
API_KEY = ADDON.getSetting('API_KEY')
USE_HD = ADDON.getSetting('USE_HD')
IS_DEBUG = ADDON.getSetting('IS_DEBUG')
STRING = ADDON.getLocalizedString
PLUGIN_BASE_URL = sys.argv[0]

def LOG(message):
    if IS_DEBUG == 'true':
        xbmc.log('Seasonvar.ru.standalone: '+str(message))

def ShowDialogBox(message):
    xbmcgui.Dialog().ok('message',message)

def ShowLettersMenu(isRussian=False):
    items = []
    if isKeyActive():
        if isRussian:
            abc = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Э', 'Ю', 'Я']
        else:
            abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z']

        for letter in abc:
            item = xbmcgui.ListItem(letter)
            sys_url = PLUGIN_BASE_URL + '?mode=get_serial_list_by_title&letter=' + letter
            itemData = (sys_url,item, True)
            items.append(itemData)
    else:
        displayMissingKeyMessage()

    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def MainMenu():
    item = xbmcgui.ListItem(STRING(30100))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_letters_menu_russian'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    item = xbmcgui.ListItem(STRING(30101))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_letters_menu_english'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    item = xbmcgui.ListItem(STRING(30109))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_favorites_menu'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def ShowFavoritesMenu():
    pass
######################################################################################
# List serial by selected letter
######################################################################################


def getSerialListByTitle(title):
    if isKeyActive():
        values = {'key': API_KEY, 'command': 'getSerialList', 'letter': urllib.unquote(title)}

        # do http request for search data
        response = getRemoteData(API_URL, values)
        response = json.loads(response)
        if isAuthorized(response):

            if isinstance(response, dict) and 'error' in response.values():
                ShowDialogBox(
                    STRING(30108)
                )
            else:
                for serial in response:
                    seasonCount = serial.get('count_of_seasons')
                    serial_title = serial.get('name')
                    serial_thumb = serial.get('poster')
                    item = None
                    if seasonCount:
                        item = xbmcgui.ListItem(serial_title+' ['+STRING(30102)+': '+seasonCount+']')
                        itemUrl = PLUGIN_BASE_URL + '?mode=get_season_list_by_title&title=' + serial_title
                    else:
                        # there are no seasons
                        item = xbmcgui.ListItem(serial_title)
                        itemUrl = PLUGIN_BASE_URL + '?mode=get_season_by_id&id=' + serial.get('last_season_id')

                    item.setIconImage(serial_thumb)
                    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, itemUrl, item, True)
        else:
            return displayUnauthorizedMessage()
    else:
        return displayMissingKeyMessage()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def getSeasonListByTitle(title):
    if isKeyActive():
        values = {
            'command': 'getSeasonList',
            'name': urllib.unquote(title),
            'key': API_KEY
        }

        response = getRemoteData(API_URL, values)
        response = json.loads(response)

        if isAuthorized(response):

            if isinstance(response, dict) and 'error' in response.values():
                ShowDialogBox(
                    STRING(30108)
                )
            else:
                items = []
                for season in response:
                    season_id = season.get('id')
                    season_number = season.get('season_number')
                    item = xbmcgui.ListItem(season.get('name')+' '+STRING(30103)+' '+season_number)
                    item.setIconImage(season.get('poster'))
                    itemUrl = PLUGIN_BASE_URL + '?mode=get_season_by_id&id=' + season_id
                    itemData = (itemUrl, item, True)
                    items.append(itemData)

                xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)

        else:
            return displayUnauthorizedMessage()
    else:
        return displayMissingKeyMessage()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def get_season_by_id(id):
    if isKeyActive():
        values = {
            'command': 'getSeason',
            'season_id': id,
            'key': API_KEY
        }

        response = getRemoteData(API_URL, values)
        response = json.loads(response)

        if isAuthorized(response):

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
                        video_link_hd = re.sub(r'http:\/\/[^.]+\.datalock\.ru','http://data-hd.datalock.ru',video_link_hd)
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
            return displayUnauthorizedMessage()
    else:
        return displayMissingKeyMessage()

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def isKeyActive():
    if API_KEY != '':
        return True

    return False


def isAuthorized(response):
    if 'error' in response:
        if (response.get('error') == 'Authentication::getUser::wrong key'):
            return False
    return True


def displayUnauthorizedMessage():
    xbmcgui.Dialog().ok(STRING(30106), STRING(30105))


def displayMissingKeyMessage():
    xbmcgui.Dialog().ok(STRING(30106), STRING(30107))

params = get_params()
if len(params) == 0:
    MainMenu()
elif params['mode'] == 'show_letters_menu_russian':
    ShowLettersMenu(isRussian=True)
elif params['mode'] == 'show_letters_menu_english':
    ShowLettersMenu(isRussian=False)
elif params['mode'] == 'get_serial_list_by_title':
    getSerialListByTitle(params['letter'])
elif params['mode'] == 'get_season_list_by_title':
    getSeasonListByTitle(params['title'])
elif params['mode'] == 'get_season_by_id':
    get_season_by_id(params['id'])
elif params['mode'] == 'show_favorites_menu':
    ShowFavoritesMenu()
else:
    MainMenu()