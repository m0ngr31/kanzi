#!/usr/bin/env python

"""
The MIT License (MIT)

Copyright (c) 2015 Maker Musings && m0ngr31

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

# For a complete discussion, see http://forum.kodi.tv/showthread.php?tid=254502

import datetime
import json
import requests
import time
import urllib
import os
import random
import re
import string
import sys
import pycountry
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


# These are words that we ignore when doing a non-exact match on show names
STOPWORDS = [
  "a",
  "about",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "how",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "this",
  "to",
  "was",
  "what",
  "when",
  "where",
  "will",
  "with",
]


# Very naive method to remove a leading "the" from the given string
def remove_the(name):
  if name[:4].lower() == "the ":
    return name[4:]
  else:
    return name


# Remove extra slashes
def http_normalize_slashes(url):
  url = str(url)
  segments = url.split('/')
  correct_segments = []
  for segment in segments:
    if segment != '':
      correct_segments.append(segment)
  first_segment = str(correct_segments[0])
  if first_segment.find('http') == -1:
    correct_segments = ['http:'] + correct_segments
  correct_segments[0] = correct_segments[0] + '/'
  normalized_url = '/'.join(correct_segments)
  return normalized_url


# These two methods construct the JSON-RPC message and send it to the Kodi player
def SendCommand(command):
  # Do not use below for your own settings, use the .env file
  SCHEME = os.getenv('KODI_SCHEME')
  if not SCHEME:
    SCHEME = 'http'
  SUBPATH = os.getenv('KODI_SUBPATH')
  if not SUBPATH:
    SUBPATH = ''
  KODI = os.getenv('KODI_ADDRESS')
  if not KODI:
    KODI = '127.0.0.1'
  PORT = os.getenv('KODI_PORT')
  if not PORT:
    PORT = '8080'
  USER = os.getenv('KODI_USERNAME')
  if not USER:
    USER = 'kodi'
  PASS = os.getenv('KODI_PASSWORD')
  if not PASS:
    PASS = 'kodi'

  # Join the environment variables into a url
  url = "%s://%s:%s/%s/%s" % (SCHEME, KODI, PORT, SUBPATH, 'jsonrpc')

  # Remove any double slashes in the url
  url = http_normalize_slashes(url)

  print "Sending request to %s" % (url)

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


# Function to convert numbers to words
def word_form(number):
  # based on stackoverflow answer from https://github.com/ralphembree/Loquitor
  leading_zero = 0
  ones = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
  tens = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
  teens = ("ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
  levels = ("", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion", "sextillion", "septillion", "octillion", "nonillion")

  word = ""
  if number[0] == "0":
    leading_zero = 1
  #number will now be the reverse of the string form of itself.
  num = reversed(str(number))
  number = ""
  for x in num:
    number += x
  del num
  if len(number) % 3 == 1:
    number += "0"
  x = 0
  for digit in number:
    if x % 3 == 0:
      word = levels[x / 3] + " " + word
      n = int(digit)
    elif x % 3 == 1:
      if digit == "1":
        num = teens[n]
      else:
        num = tens[int(digit)]
        if n:
          if num:
            num += " " + ones[n]
          else:
            num = ones[n]
      word = num + " " + word
    elif x % 3 == 2:
      if digit != "0":
        word = ones[int(digit)] + " hundred and " + word
    x += 1
  reply = word.strip(", ")
  if leading_zero:
    reply = "zero " +reply
  return reply


# Function to replace the digits in the Alexa heard term to words
def replaceDigits(phrase):
  # all word variant of the heard phrase if it contains digits
  wordified = ''
  for word in phrase.split():
    word = word.decode('utf-8')
    if word.isnumeric():
      word = word_form(word)
    wordified = wordified + word + " "
  return wordified[:-1]


# Match heard string to something in the results
def matchHeard(heard, results, lookingFor='label'):
  located = None

  heard_minus_the = remove_the(heard)
  print heard
  sys.stdout.flush()
  heard_list = set([x for x in heard.split() if x not in STOPWORDS])

  for result in results:
    # Strip out non-ascii symbols and lowercase it
    ascii_name = result[lookingFor].encode('ascii', 'replace')
    result_name = str(ascii_name).lower().translate(None, string.punctuation)

    # Direct comparison
    if heard == result_name:
      located = result
      break

    # Remove 'the'
    if remove_the(result_name) == heard_minus_the:
      located = result
      break

    # Remove parentheses
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    if heard == removed_paren:
      located = result
      break

  if not located:
    print 'not located on the first round of checks'
    sys.stdout.flush()
    # Loop through results again and be a little more liberal with what is accepted
    for result in results:
      # Strip out non-ascii symbols and lowercase it
      ascii_name = result[lookingFor].encode('ascii', 'replace')
      result_name = str(ascii_name).lower().translate(None, string.punctuation)

      #print "trying '%s'" % (heard_minus_the)
      #sys.stdout.flush()
      #print result_name
      #sys.stdout.flush()
      # Just look for substring
      if result_name.find(heard_minus_the) != -1:
        located = result
        break

      # Last resort -- take out some useless words and see if we have a match with
      # >= 60% of the heard phrase
      result_list = set([x for x in result_name.split() if x not in STOPWORDS])
      matched_words = [x for x in heard_list if x in result_list]
      #print 'matched words: '
      #sys.stdout.flush()
      if len(matched_words) > 0:
        print matched_words
        sys.stdout.flush()
        percentage = float(len(matched_words)) / float(len(heard_list))
        if percentage > float(0.6):
          located = result
          break

    if not located:
      print 'not located on the second round of checks'
      sys.stdout.flush()
      fuzzy_result = process.extract(str(heard), [d['label'] for d in results], limit=1, scorer=fuzz.QRatio)
      if fuzzy_result[0][1] > 75:
        located = (item for item in results if item['label'] == fuzzy_result[0][0]).next()
      else:
        fuzzy_result = process.extract(str(heard), [d['label'] for d in results], limit=1, scorer=fuzz.partial_ratio)
        if fuzzy_result[0][1] > 75:
          located = (item for item in results if item['label'] == fuzzy_result[0][0]).next()
        else:
          heard = replaceDigits(heard)
          fuzzy_result = process.extract(str(heard), [d['label'] for d in results], limit=1, scorer=fuzz.QRatio)
          if fuzzy_result[0][1] > 75:
            located = (item for item in results if item['label'] == fuzzy_result[0][0]).next()
          else:
            fuzzy_result = process.extract(str(heard), [d['label'] for d in results], scorer=fuzz.partial_ratio)
            if fuzzy_result[0][1] > 75:
              located = (item for item in results if item['label'] == fuzzy_result[0][0]).next()

  return located


# Playlists

def ClearPlaylist():
  return SendCommand(RPCString("Playlist.Clear", {"playlistid": 0}))


def ClearVideoPlaylist():
  return SendCommand(RPCString("Playlist.Clear", {"playlistid": 1}))


def StartPlaylist(playlist_file=None):
  if playlist_file is not None and playlist_file != '':
    return SendCommand(RPCString("Player.Open", {"item": {"file": playlist_file}}))
  else:
    return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 0}}))


def AddSongToPlaylist(song_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": {"songid": int(song_id)}}))


def AddAlbumToPlaylist(album_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 0, "item": {"albumid": int(album_id)}}))


def PrepEpisodePlayList(ep_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"episodeid": int(ep_id)}}))


def PrepMoviePlaylist(movie_id):
  return SendCommand(RPCString("Playlist.Add", {"playlistid": 1, "item": {"movieid": int(movie_id)}}))


def StartVideoPlaylist():
  return SendCommand(RPCString("Player.Open", {"item": {"playlistid": 1}}))


def PlayEpisode(ep_id, resume=True):
  return SendCommand(RPCString("Player.Open", {"item": {"episodeid": ep_id}, "options": {"resume": resume}}))


def PlayMovie(movie_id, resume=True):
  return SendCommand(RPCString("Player.Open", {"item": {"movieid": movie_id}, "options": {"resume": resume}}))


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


def CleanVideo():
  return SendCommand(RPCString("VideoLibrary.Clean"))


def UpdateMusic():
  return SendCommand(RPCString("AudioLibrary.Scan"))


def CleanMusic():
  return SendCommand(RPCString("AudioLibrary.Clean"))


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


def ToggleFullscreen():
  return SendCommand(RPCString("GUI.SetFullscreen", {"fullscreen":"toggle"}))


def ToggleMute():
  return SendCommand(RPCString("Application.SetMute", {"mute":"toggle"}))


# Player controls

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


def PlayerSeekSmallForward():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"smallforward"}))


def PlayerSeekSmallBackward():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"smallbackward"}))


def PlayerSeekBigForward():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"bigforward"}))


def PlayerSeekBigBackward():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"bigbackward"}))


def Replay():
  playerid = GetPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Seek", {"playerid":playerid, "value":"smallbackward"}))


def SubtitlesOn():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetSubtitle", {"playerid":playerid, "subtitle":"on"}))


def SubtitlesOff():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetSubtitle", {"playerid":playerid, "subtitle":"off"}))


def SubtitlesNext():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetSubtitle", {"playerid":playerid, "subtitle":"next", "enable":True}))


def SubtitlesPrevious():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetSubtitle", {"playerid":playerid, "subtitle":"previous", "enable":True}))


def AudioStreamNext():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetAudioStream", {"playerid":playerid, "stream":"next"}))


def AudioStreamPrevious():
  playerid = GetVideoPlayerID()
  if playerid:
    return SendCommand(RPCString("Player.SetAudioStream", {"playerid":playerid, "stream":"previous"}))


def PlayerMoveUp():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Move", {"playerid":playerid, "direction":"up"}))


def PlayerMoveDown():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Move", {"playerid":playerid, "direction":"down"}))


def PlayerMoveLeft():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Move", {"playerid":playerid, "direction":"left"}))


def PlayerMoveRight():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Move", {"playerid":playerid, "direction":"right"}))


def PlayerZoom(lvl=0):
  playerid = GetPicturePlayerID()
  if playerid and lvl > 0 and lvl < 11:
    return SendCommand(RPCString("Player.Zoom", {"playerid":playerid, "zoom":lvl}))


def PlayerZoomIn():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Zoom", {"playerid":playerid, "zoom":"in"}))


def PlayerZoomOut():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Zoom", {"playerid":playerid, "zoom":"out"}))


def PlayerRotateClockwise():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Rotate", {"playerid":playerid, "value":"clockwise"}))


def PlayerRotateCounterClockwise():
  playerid = GetPicturePlayerID()
  if playerid:
    return SendCommand(RPCString("Player.Rotate", {"playerid":playerid, "value":"counterclockwise"}))


# Addons

def CallKodiSearch(name=''):
  return SendCommand(RPCString("Addons.ExecuteAddon", {"addonid": "script.globalsearch", "params":{"searchstring":name}}))


def CinemaVision():
  return SendCommand(RPCString("Addons.ExecuteAddon", { "addonid": "script.cinemavision", "params": ["experience"]}))


# Library queries

def GetMusicPlaylists():
  return SendCommand(RPCString("Files.GetDirectory", {"directory": "special://musicplaylists"}))


def GetMusicArtists():
  return SendCommand(RPCString("AudioLibrary.GetArtists"))


def GetMusicGenres():
  return SendCommand(RPCString("AudioLibrary.GetGenres"))


def GetArtistAlbums(artist_id):
  return SendCommand(RPCString("AudioLibrary.GetAlbums", {"filter": {"artistid": int(artist_id)}}))


def GetAlbums():
  return SendCommand(RPCString("AudioLibrary.GetAlbums"))


def GetAllSongs():
  return SendCommand(RPCString("AudioLibrary.GetSongs"))


def GetArtistSongs(artist_id):
  return SendCommand(RPCString("AudioLibrary.GetSongs", {"filter": {"artistid": int(artist_id)}}))


def GetRecentlyAddedSongs():
  return SendCommand(RPCString("AudioLibrary.GetRecentlyAddedSongs"))


def GetTvShowDetails(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetTVShowDetails", {'tvshowid':show_id, 'properties':['art']}))
  return data['result']['tvshowdetails']


def GetTvShows():
  return SendCommand(RPCString("VideoLibrary.GetTVShows"))


def GetMovieDetails(movie_id):
  data = SendCommand(RPCString("VideoLibrary.GetMovieDetails", {'movieid':movie_id, 'properties':['resume']}))
  return data['result']['moviedetails']


def GetMovies():
  return SendCommand(RPCString("VideoLibrary.GetMovies"))


def GetMoviesByGenre(genre):
  return SendCommand(RPCString("VideoLibrary.GetMovies", {"filter":{"genre":genre}}))


def GetMovieGenres():
  return SendCommand(RPCString("VideoLibrary.GetGenres", {"type": "movie"}))


def GetEpisodeDetails(ep_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodeDetails", {"episodeid": int(ep_id), "properties":["season", "episode", "resume"]}))
  return data['result']['episodedetails']


def GetEpisodesFromShow(show_id):
  return SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id)}))


def GetUnwatchedEpisodesFromShow(show_id):
  return SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}}))


def GetNewestEpisodeFromShow(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1},"tvshowid": int(show_id), "sort":{"method":"dateadded", "order":"descending"}}))
  if 'episodes' in data['result']:
    episode = data['result']['episodes'][0]
    return episode['episodeid']
  else:
    return None


def GetNextUnwatchedEpisode(show_id):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1},"tvshowid": int(show_id), "filter":{"field":"lastplayed", "operator":"greaterthan", "value":"0"}, "properties":["season", "episode", "lastplayed", "firstaired", "resume"], "sort":{"method":"lastplayed", "order":"descending"}}))
  if 'episodes' in data['result']:
    episode = data['result']['episodes'][0]
    episode_season = episode['season']
    episode_number = episode['episode']

    resume = episode['resume']['position']
    if resume > 0:
      next_episode_id = episode['episodeid']
    else:
      next_episode_id = GetSpecificEpisode(show_id, episode_season, int(episode_number) + 1)

    if next_episode_id:
      return next_episode_id
    else:
      next_episode_id = GetSpecificEpisode(show_id, int(episode_season) + 1, 1)

      if next_episode_id:
        return next_episode_id
      else:
        return None
  else:
    return None


def GetLastWatchedShow():
  return SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":1}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "filter":{"field":"lastplayed", "operator":"greaterthan", "value":"0"}, "sort":{"method":"lastplayed", "order":"descending"}, "properties":["tvshowid", "showtitle"]}))


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
  return SendCommand(RPCString("VideoLibrary.GetEpisodes", {"tvshowid": int(show_id), "properties": ["season", "episode"]}))


# Returns a list of dictionaries with information about episodes that have been watched.
# May take a long time if you have lots of shows and you set max to a big number
def GetWatchedEpisodes(max=90):
  return SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"greaterthan", "value":"0"}, "properties":["playcount", "showtitle", "season", "episode", "lastplayed" ]}))


# Returns a list of dictionaries with information about unwatched movies. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.
def GetUnwatchedMovies(max=90):
  data = SendCommand(RPCString("VideoLibrary.GetMovies", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "dateadded" ]}))
  answer = []
  for d in data['result']['movies']:
    answer.append({'title':d['title'], 'movieid':d['movieid'], 'label':d['label'], 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
  return answer

# Returns a list of dictionaries with information about unwatched movies in a particular genre. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.
def GetUnwatchedMoviesByGenre(genre, max=90):
  data = SendCommand(RPCString("VideoLibrary.GetMovies", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "filter":{"genre":genre}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "dateadded" ]}))
  answer = []
  for d in data['result']['movies']:
    answer.append({'title':d['title'], 'movieid':d['movieid'], 'label':d['label'], 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
  return answer


# Returns a list of dictionaries with information about unwatched episodes. Useful for
# telling/showing users what's ready to be watched. Setting max to very high values
# can take a long time.
def GetUnwatchedEpisodes(max=90):
  data = SendCommand(RPCString("VideoLibrary.GetEpisodes", {"limits":{"end":max}, "filter":{"field":"playcount", "operator":"lessthan", "value":"1"}, "sort":{"method":"dateadded", "order":"descending"}, "properties":["title", "playcount", "showtitle", "tvshowid", "dateadded" ]}))
  answer = []
  shows = set([d['tvshowid'] for d in data['result']['episodes']])
  show_info = {}
  for show in shows:
    show_info[show] = GetTvShowDetails(show_id=show)
  for d in data['result']['episodes']:
    showinfo = show_info[d['tvshowid']]
    answer.append({'title':d['title'], 'episodeid':d['episodeid'], 'show':d['showtitle'], 'label':d['label'], 'dateadded':datetime.datetime.strptime(d['dateadded'], "%Y-%m-%d %H:%M:%S")})
  return answer


# System commands
def ApplicationQuit():
  return SendCommand(RPCString("Application.Quit"))

def SystemHibernate():
  return SendCommand(RPCString("System.Hibernate"))

def SystemReboot():
  return SendCommand(RPCString("System.Reboot"))

def SystemShutdown():
  return SendCommand(RPCString("System.Shutdown"))

def SystemSuspend():
  return SendCommand(RPCString("System.Suspend"))

def SystemEjectMedia():
  return SendCommand(RPCString("System.EjectOpticalDrive"))


# Misc helpers

# Get the first active player.
def GetPlayerID(playertype=['audio', 'video', 'picture']):
  data = SendCommand(RPCString("Player.GetActivePlayers"))
  result = data.get("result", [])
  if len(result) > 0:
    for curitem in result:
      if curitem.get("type") in playertype:
        return curitem.get("playerid")
  return None

# Get the first active Video player.
def GetVideoPlayerID(playertype=['video']):
  data = SendCommand(RPCString("Player.GetActivePlayers"))
  result = data.get("result", [])
  if len(result) > 0:
    for curitem in result:
      if curitem.get("type") in playertype:
        return curitem.get("playerid")
  return None


# Get the first active Audio player.
def GetAudioPlayerID(playertype=['audio']):
  data = SendCommand(RPCString("Player.GetActivePlayers"))
  result = data.get("result", [])
  if len(result) > 0:
    for curitem in result:
      if curitem.get("type") in playertype:
        return curitem.get("playerid")
  return None


# Get the first active Picture player.
def GetPicturePlayerID(playertype=['picture']):
  data = SendCommand(RPCString("Player.GetActivePlayers"))
  result = data.get("result", [])
  if len(result) > 0:
    for curitem in result:
      if curitem.get("type") in playertype:
        return curitem.get("playerid")
  return None


# Information about the video or audio that's currently playing

def GetActivePlayItem():
  playerid = GetPlayerID()
  if playerid is not None:
    data = SendCommand(RPCString("Player.GetItem", {"playerid":playerid, "properties":["title", "album", "artist", "season", "episode", "showtitle", "tvshowid", "description"]}))
    #print data['result']['item']
    return data['result']['item']


def GetActivePlayProperties():
  playerid = GetPlayerID()
  if playerid is not None:
    data = SendCommand(RPCString("Player.GetProperties", {"playerid":playerid, "properties":["currentaudiostream", "currentsubtitle", "canshuffle", "shuffled", "canrepeat", "repeat", "canzoom", "canrotate", "canmove"]}))
    #print data['result']
    return data['result']


# Returns current subtitles as a speakable string
def GetCurrentSubtitles():
  subs = ""
  curprops = GetActivePlayProperties()
  if curprops is not None:
    try:
      lang = curprops['currentsubtitle']['language']
      subs = pycountry.languages.get(bibliographic=lang).name
      name = curprops['currentsubtitle']['name']
      if name:
        subs += " " + name
    except:
      pass
  return subs


# Returns current audio stream as a speakable string
def GetCurrentAudioStream():
  stream = ""
  curprops = GetActivePlayProperties()
  if curprops is not None:
    try:
      lang = curprops['currentaudiostream']['language']
      stream = pycountry.languages.get(bibliographic=lang).name
      name = curprops['currentaudiostream']['name']
      if name:
        stream += " " + name
    except:
      pass
  return stream


# Returns information useful for building a progress bar to show an item's play time
def GetPlayerStatus():
  playerid = GetVideoPlayerID()
  if playerid is None:
    playerid = GetAudioPlayerID()
  if playerid is not None:
    data = SendCommand(RPCString("Player.GetProperties", {"playerid":playerid, "properties":["percentage", "speed", "time", "totaltime"]}))
    if 'result' in data:
      hours_total = data['result']['totaltime']['hours']
      hours_cur = data['result']['time']['hours']
      mins_total = hours_total * 60 + data['result']['totaltime']['minutes']
      mins_cur = hours_cur * 60 + data['result']['time']['minutes']
      speed = data['result']['speed']
      if hours_total > 0:
        total = '%d:%02d:%02d' % (hours_total, data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
        cur = '%d:%02d:%02d' % (data['result']['time']['hours'], data['result']['time']['minutes'], data['result']['time']['seconds'])
      else:
        total = '%02d:%02d' % (data['result']['totaltime']['minutes'], data['result']['totaltime']['seconds'])
        cur = '%02d:%02d' % (data['result']['time']['minutes'], data['result']['time']['seconds'])
      return {'state':'play' if speed > 0 else 'pause', 'time':cur, 'time_hours':hours_cur, 'time_mins':mins_cur, 'totaltime':total, 'total_hours':hours_total, 'total_mins':mins_total, 'pct':data['result']['percentage']}
  return {'state':'stop'}
