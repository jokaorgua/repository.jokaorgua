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

ADDONID = 'plugin.video.seasonvar.ru.standalone'
API_URL = "http://api.seasonvar.ru/"
PLUGIN_HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id=ADDONID)
ADDONFILEPATH    = xbmc.translatePath( ADDON.getAddonInfo('profile') )
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
API_KEY = ADDON.getSetting('API_KEY')
USE_HD = ADDON.getSetting('USE_HD')
IS_DEBUG = ADDON.getSetting('IS_DEBUG')
STRING = ADDON.getLocalizedString
PLUGIN_BASE_URL = sys.argv[0]
FAVORITES_FILEPATH = ADDONFILEPATH+'/'+ADDONID+'_favorites.json'

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
    if not os.path.exists(FAVORITES_FILEPATH) or not os.path.isfile(FAVORITES_FILEPATH):
        try:
            with open(FAVORITES_FILEPATH,'a') as f:
                f.write('{}')
                f.close()
        except:
            LOG(sys.exc_info())
            ShowDialogBox('Can not create favorites file. WTF??? ' + FAVORITES_FILEPATH)
            return

    item = xbmcgui.ListItem(STRING(30100))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_letters_menu_russian'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    item = xbmcgui.ListItem(STRING(30101))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_letters_menu_english'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    item = xbmcgui.ListItem(STRING(30109))
    menuUrl = PLUGIN_BASE_URL + '?mode=show_favorites_menu'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    item = xbmcgui.ListItem(STRING(30115))
    menuUrl = PLUGIN_BASE_URL + '?mode=updates'
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, menuUrl, item, True)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def Updates():
    favoritesData = {}
    fp = None
    try:
        fpRead = open(FAVORITES_FILEPATH)

        favoritesData = json.load(fpRead)
    except:
        LOG('Can not load json data from favorites file')
        ShowDialogBox(STRING(30106))
        return
    items = []

    for serial_title in favoritesData.keys():
        serial_data = getFullSerialData(serial_title.encode('utf-8'))
        for season_id in serial_data['seasons'].keys():
            for part in serial_data['seasons'][season_id]['series'].keys():
                try:
                    a = favoritesData[serial_title]['seasons'][unicode(str(season_id),'utf-8')][u'series'][unicode(str(part),'utf-8')]
                except:
                    item = xbmcgui.ListItem(serial_title+" "+serial_data['seasons'][season_id][u'series'][part]['name'])
                    video_link = PLUGIN_BASE_URL + "?mode=playlink&serial_title="+urllib.quote(serial_title.encode('utf-8'))+"&url="+urllib.quote(serial_data['seasons'][season_id]['series'][part]['link'])
                    itemData = (video_link, item, False)
                    items.append(itemData)
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

def PlayLink(url, serial_title):
    serial_title = urllib.unquote(serial_title)
    url = urllib.unquote(url)
    try:
        if USE_HD == 'true':
            video_link_hd = url.replace('7f_','hd_')
            video_link_hd = re.sub(r'http:\/\/[^.]+\.datalock\.ru','http://data-hd.datalock.ru',video_link_hd)
            LOG('video link converted to HD '+video_link_hd)
            if remoteFileExists(video_link_hd):
                url = video_link_hd
    except:
        LOG('Problem in converting video link to HD '+str(sys.exc_info()))
    listItem = xbmcgui.ListItem("PlayLink", path=url)
    RemoveFromFavorites(serial_title)
    AddToFavorites(serial_title)
    xbmc.Player().play(item=url, listitem=listItem)

def AddToFavorites(title):
    title = urllib.unquote(title)
    favoritesData = {}
    fp = None
    try:
        fpRead = open(FAVORITES_FILEPATH)

        favoritesData = json.load(fpRead)
    except:
        LOG('Can not load json data from favorites file')
        ShowDialogBox(STRING(30106))
        return
    if favoritesData.has_key(unicode(title,'utf-8')):
        ShowDialogBox(STRING(30113))
        return
    favoritesData[title] = getFullSerialData(title)
    fpRead.close()
    fpWrite = open(FAVORITES_FILEPATH,'w')
    json.dump(favoritesData,fpWrite)

    fpWrite.close()
    return

def RemoveFromFavorites(title):
    title = urllib.unquote(title)
    favoritesData = {}
    fp = None
    try:
        fpRead = open(FAVORITES_FILEPATH)

        favoritesData = json.load(fpRead)
    except:
        LOG('Can not load json data from favorites file')
        ShowDialogBox(STRING(30106))
        return
    del favoritesData[unicode(title,'utf-8')]
    fpRead.close()
    fpWrite = open(FAVORITES_FILEPATH,'w')
    json.dump(favoritesData,fpWrite)

    fpWrite.close()
    ShowFavoritesMenu()

def getFullSerialData(title):
    serialData = {}
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
                serialData['seasons'] = {}
                for season in response:
                    season_id = season.get('id')
                    season_number = season.get('season_number')
                    serialData['seasons'][season_id] = getSeasonSeriesById(season_id)

            return serialData

        else:
            return displayUnauthorizedMessage()
    else:
        return displayMissingKeyMessage()


def ShowFavoritesMenu():
    if not os.path.exists(FAVORITES_FILEPATH) or not os.path.isfile(FAVORITES_FILEPATH):
        LOG('Favorites file does not exist. '+FAVORITES_FILEPATH)
        ShowDialogBox(STRING(30110))
    data = open(FAVORITES_FILEPATH).read()
    LOG(data)
    if len(data) < 2:
        LOG('Favorites data file too small. '+data)
        ShowDialogBox(STRING(30111))
        return
    try:
        favoritesData = json.loads(data)
    except:
        LOG('Can not load json data from favorites file '+data)
        ShowDialogBox(STRING(30106))
        return
    items = []
    for data in favoritesData.keys():
        item = xbmcgui.ListItem(data)
        if len(favoritesData[data]['seasons'].keys()) > 1:
            itemUrl = PLUGIN_BASE_URL + '?mode=get_season_list_by_title&title='+data
        else:
            itemUrl = PLUGIN_BASE_URL + '?mode=get_season_by_id&id='+favoritesData[data]['seasons'].keys()[0]
        commands = []
        commands.append(( STRING(30114), 'XBMC.RunPlugin('+PLUGIN_BASE_URL + '?mode=remove_from_favorites&title=' + urllib.quote(data.encode('utf-8'))+')', ))
        item.addContextMenuItems( commands, True )
        itemData = (itemUrl,item,True)
        items.append(itemData)
    xbmcplugin.addDirectoryItems(PLUGIN_HANDLE, items)
    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
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
                    commands = []
                    commands.append(( STRING(30112), 'XBMC.RunPlugin('+PLUGIN_BASE_URL + '?mode=add_to_favorites&title=' + urllib.quote(serial_title.encode('utf-8'))+')', ))
                    item.addContextMenuItems( commands, True )
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


def getSeasonSeriesById(id):
    seasonData = {}
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
            seasonData['series'] = {}
            i = 1
            for video in playlist:
                video_name = video.get('name')

                video_link = video.get('link')
                seasonData['series'][i] = {}
                seasonData['series'][i]['name'] = video_name

                seasonData['series'][i]['link'] = video_link
                i += 1

            return seasonData

        else:
            return displayUnauthorizedMessage()
    else:
        return displayMissingKeyMessage()


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
elif params['mode'] == 'add_to_favorites':
    AddToFavorites(params['title'])
elif params['mode'] == 'remove_from_favorites':
    RemoveFromFavorites(params['title'])
elif params['mode'] == 'updates':
    Updates()
elif params['mode'] == 'playlink':
    PlayLink(params['url'], params['serial_title'])
else:
    MainMenu()