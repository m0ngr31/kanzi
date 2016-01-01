#!/usr/bin/env python

"""
The MIT License (MIT)

Copyright (c) 2015 Maker Musings & m0ngr31

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# For a complete discussion, see http://www.makermusings.com

import datetime
import json
import requests
import time
import urllib
import os
import random

# These two methods construct the JSON-RPC message and send it to the Kodi player

def SendCommand(command):
    # Change this to the IP address of your Kodi server or always pass in an address
    KODI = os.getenv('KODI_ADDRESS', '127.0.0.1')
    PORT = int(os.getenv('KODI_PORT', 8089))
    USER = os.getenv('KODI_USERNAME', 'kodi')
    PASS = os.getenv('KODI_PASSWORD', '')
    
    url = "http://%s:%d/jsonrpc" % (KODI, PORT)
    try:
        r = requests.post(url, data=command, auth=(USER, PASS))
    except:
        return {}
    return json.loads(r.text)

def RPCString(method, params=None):
    j = {"jsonrpc":"2.0", "method":method, "id":1}
    if params:
        j["params"] = params
    return json.dumps(j)


# This is a little weak because if there are multiple active players,
# it only returns the first one and assumes it's the one you want.
# In practice, this works OK in common cases.

def GetPlayerID():
    info = SendCommand(RPCString("Player.GetActivePlayers"))
    result = info.get("result", [])
    if len(result) > 0:
        return result[0].get("playerid")
    else:
        return None
        
def ClearPlaylist():
    return SendCommand(RPCString("Playlist.Clear", {"playlistid": 0}))
    
def ClearVideoPlaylist():
    return SendCommand(RPCString("Playlist.Clear", {"playlistid": 1}))

def StartPlaylist():
    return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 0}}))
    
def AddSongToPlaylist(song_id):
    return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": {"songid": int(song_id)}}))
    
def PrepEpisodePlayList(ep_id):
    return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"episodeid": int(ep_id)}}))

def PrepMoviePlaylist(movie_id):
   return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"movieid": int(movie_id)}}))
   
def StartVideoPlaylist():
    return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 1}}))

def AddSongsToPlaylist(song_ids):
    songs_array = []
    
    for song_id in song_ids:
        temp_song = {}
        temp_song['songid'] = song_id
        songs_array.append(temp_song)
    
    random.shuffle(songs_array)
        
    return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": songs_array}))

def GetPlaylistItems():
    return SendCommand(RPCString("Playlist.GetItems", {"playlistid": 0}))
    
def GetVideoPlaylistItems():
    return SendCommand(RPCString("Playlist.GetItems", {"playlistid": 1}))
    

# Tell Kodi to update its video or music libraries

def UpdateVideo():
    return SendCommand(RPCString("VideoLibrary.Scan"))

def UpdateMusic():
    return SendCommand(RPCString("AudioLibrary.Scan"))



# Perform UI actions that match the normal remote control buttons

def PageUp():
    return SendCommand(RPCString("Input.ExecuteAction", {"action":"pageup"}))

def PageDown():
    return SendCommand(RPCString("Input.ExecuteAction", {"action":"pagedown"}))

def ToggleWatched():
    return SendCommand(RPCString("Input.ExecuteAction", {"action":"togglewatched"}))

def Info():
    return SendCommand(RPCString("Input.Info"))

def Menu():
    return SendCommand(RPCString("Input.ContextMenu"))

def Home():
    return SendCommand(RPCString("Input.Home"))

def Select():
    return SendCommand(RPCString("Input.Select"))

def Up():
    return SendCommand(RPCString("Input.Up"))

def Down():
    return SendCommand(RPCString("Input.Down"))

def Left():
    return SendCommand(RPCString("Input.Left"))

def Right():
    return SendCommand(RPCString("Input.Right"))

def Back():
    return SendCommand(RPCString("Input.Back"))

def PlayPause():
    playerid = GetPlayerID()
    if playerid is not None:
        return SendCommand(RPCString("Player.PlayPause", {"playerid":playerid}))
        
def PlaySkip():
    playerid = GetPlayerID()
    if playerid is not None:
        return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "next"}))
        
def PlayPrev():
    playerid = GetPlayerID()
    if playerid is not None:
        SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))
        return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))
        
def PlayStartOver():
    playerid = GetPlayerID()
    if playerid is not None:
        return SendCommand(RPCString("Player.GoTo", {"playerid":playerid, "to": "previous"}))

def Stop():
    playerid = GetPlayerID()
    if playerid is not None:
        return SendCommand(RPCString("Player.Stop", {"playerid":playerid}))

def Replay():
    playerid = GetPlayerID()
    if playerid:
        return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"smallbackward"}))
        
def GetMusicArtists():
    data = SendCommand(RPCString("AudioLibrary.GetArtists"))
    return data

def GetArtistAlbums(artist_id):
    data = SendCommand(RPCString("AudioLibrary.GetAlbums", {"filter": {"artistid": int(artist_id)}}))
    return data
    
def GetArtistSongs(artist_id):
    data = SendCommand(RPCString("AudioLibrary.GetSongs", {"filter": {"artistid": int(artist_id)}}))
    return data

def GetTvShows():
    data = SendCommand(RPCString("VideoLibrary.GetTVShows"))
    return data
    
def GetMovies():
    data = SendCommand(RPCString("VideoLibrary.GetMovies"))
    return data

def GetEpisodesFromShow(show_id):
    data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id)}))
    return data
    
def GetSpecificEpisode(show_id, season, episode):
    data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "season": int(season), "properties": ["season", "episode"]}))
    if 'episodes' in data['result']:
        correct_id = None
        for episode_data in data['result']['episodes']:
            if int(episode_data['episode']) == int(episode):
                correct_id = episode_data['episodeid']
                break
                
        return correct_id
    else:
        return None
    
def GetEpisodesFromShowDetails(show_id):
    data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "properties": ["season", "episode"]}))
    return data
    
# Returns a list of dictionaries with information about episodes that have been watched. 
# May take a long time if you have lots of shows and you set max to a big number

def GetWatchedEpisodes(max=90):
    data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "properties":["playcount", "showtitle", "season", "episode", "lastplayed" ]}))
    return data['result']['episodes']


# Returns a list of dictionaries with information about unwatched episodes. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.

def GetUnwatchedEpisodes(max=90):
    data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "showtitle", "tvshowid", "dateadded" ]}))
    answer = []
    shows = set([d['tvshowid'] for d in data['result']['episodes']])
    show_info = {}
    for show in shows:
        show_info[show] = GetShowDetails(show=show)
    for d in data['result']['episodes']:
        showinfo = show_info[d['tvshowid']]
        banner = ''
        if 'banner' in showinfo['art']:
            banner = "http://%s:%s/image/%s" % (urllib.quote(showinfo['art']['banner']))
        answer.append({'title':d['title'], 'episodeid':d['episodeid'], 'show':d['showtitle'], 'label':d['label'], 'banner':banner, 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
    return answer


# Grabs the artwork for the specified show. Could be modified to return other interesting data.

def GetShowDetails(show=0):
    data = SendCommand(RPCString("VideoLibrary.GetTVShowDetails", {'tvshowid':show, 'properties':['art']}))
    return data['result']['tvshowdetails']


# Information about the video that's currently playing

def GetVideoPlayItem():
    playerid = GetPlayerID()
    if playerid:
        data = SendCommand(RPCString("Player.GetItem", {"playerid":playerid, "properties":["episode","showtitle", "tvshowid", "season", "description"]}))
        return data["result"]["item"]


# Returns information useful for building a progress bar to show a video's play time

def GetVideoPlayStatus():
    playerid = GetPlayerID()
    if playerid:
        data = SendCommand(RPCString("Player.GetProperties", {"playerid":playerid, "properties":["percentage","speed","time","totaltime"]}))
        if 'result' in data:
            hours = data['result']['totaltime']['hours']
            speed = data['result']['speed']
            if hours > 0:
                total = '%d:%02d:%02d' % (hours, data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
                cur = '%d:%02d:%02d' % (data['result']['time']['hours'], data['result']['time']['minutes'], data['result']['time']['seconds'])
            else:
                total = '%02d:%02d' % (data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
                cur = '%02d:%02d' % (data['result']['time']['minutes'], data['result']['time']['seconds'])
            return {'state':'play' if speed > 0 else 'pause', 'time':cur, 'total':total, 'pct':data['result']['percentage']}
    return {'state':'stop'}

