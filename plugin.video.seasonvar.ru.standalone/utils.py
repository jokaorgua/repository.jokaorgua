import urllib2
import urllib
import sys
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

class HeadRequest(urllib2.Request):
     def get_method(self):
         return "HEAD"

def getRemoteData(url, postData):

    headers = { 'User-Agent' : USER_AGENT }
    req = urllib2.Request(url, urllib.urlencode(postData), headers)
    html = urllib2.urlopen(req).read()

    return html

def remoteFileExists(url):

    ret = urllib2.urlopen(HeadRequest(url))
    if ret.code == 200:
        return True

    return False