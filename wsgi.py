#!/usr/bin/python
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pvr

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
import os.path
import random
import re
import string
import sys
import threading
from yaep import populate_env
from yaep import env

sys.path += [os.path.dirname(__file__)]

try:
  import aniso8601
  import verifier
except:
  # cert/appid verification dependencies are optional installs
  pass

import kodi


ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

def setup_env():
  os.environ['ENV_FILE'] = ENV_FILE
  populate_env()
  #print os.environ


# These utility functions construct the required JSON for a full Alexa Skills Kit response

def build_response(session_attributes, speechlet_response):
  return {
    'version': '1.0',
    'sessionAttributes': session_attributes,
    'response': speechlet_response
  }

def build_speechlet_response(title, output, reprompt_text, should_end_session):
  response = {}
  if output:
    response['outputSpeech'] = {
      'type': 'PlainText',
      'text': output
    }
    if title:
      response['card'] = {
        'type': 'Simple',
        'title': title,
        'content': output
      }
  if reprompt_text:
    response['reprompt'] = {
      'outputSpeech': {
        'type': 'PlainText',
        'text': reprompt_text
      }
    }
  response['shouldEndSession'] = should_end_session

  return response

def build_alexa_response(speech = None, card_title = None, session_attrs = None, reprompt_text = None, end_session = True):
  return build_response(session_attrs, build_speechlet_response(card_title, speech, reprompt_text, end_session))


# Utility function to sanitize a TV Show name (e.g., strip out symbols)

RE_SHOW_WITH_PARAM = re.compile(r"(.*) \([^)]+\)$")

def sanitize_show(show_name):
  m = RE_SHOW_WITH_PARAM.match(show_name)
  if m:
    return m.group(1)
  return show_name


# Handle the CheckNewShows intent

def alexa_check_new_episodes(slots):
  card_title = 'Looking for new shows to watch'
  print card_title
  sys.stdout.flush()

  # Get the list of unwatched EPISODES from Kodi
  new_episodes = kodi.GetUnwatchedEpisodes()

  # Find out how many EPISODES were recently added and get the names of the SHOWS
  really_new_episodes = [x for x in new_episodes if x['dateadded'] >= datetime.datetime.today() - datetime.timedelta(5)]
  really_new_show_names = list(set([sanitize_show(x['show']) for x in really_new_episodes]))

  if len(really_new_episodes) == 0:
    answer = "There isn't anything new to watch."
  elif len(really_new_show_names) == 1:
    # Only one new show, so provide the number of episodes also.
    count = len(really_new_episodes)
    if count == 1:
      answer = "There is one new episide of %(show)s to watch." % {"show":really_new_show_names[0]}
    else:
      answer = "You have %(count)d new episides of %(show)s." % {'count':count, 'show':really_new_show_names[0]}
  elif len(really_new_show_names) == 2:
    random.shuffle(really_new_show_names)
    answer = "There are new episodes of %(show1)s and %(show2)s." % {'show1':really_new_show_names[0], 'show2':really_new_show_names[1]}
  elif len(really_new_show_names) > 2:
    show_sample = random.sample(really_new_show_names, 2)
    answer = "You have %(show1)s, %(show2)s, and more waiting to be watched." % {'show1':show_sample[0], 'show2':show_sample[1]}
  return build_alexa_response(answer, card_title)


# Handle the NewShowInquiry intent.

def alexa_new_show_inquiry(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)

  card_title = "Looking for new episodes of %s" % (heard_show)
  print card_title
  sys.stdout.flush()

  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']

    located = kodi.matchHeard(heard_show, shows_array)

    if located:
      episodes_result = kodi.GetUnwatchedEpisodesFromShow(located['tvshowid'])

      if not 'episodes' in episodes_result['result']:
        num_of_unwatched = 0

      else:
        num_of_unwatched = len(episodes_result['result']['episodes'])

      if num_of_unwatched > 0:
        if num_of_unwatched == 1:
          return build_alexa_response("There is one unseen episode of %(real_show)s." % {'real_show': heard_show}, card_title)
        else:
          return build_alexa_response("There are %(num)d episodes of  %(real_show)s." % {'real_show': heard_show, 'num': num_of_unwatched}, card_title)

      else:
        return build_alexa_response("There are no unseen episodes of %(real_show)s." % {'real_show': heard_show}, card_title)
    else:
      return build_alexa_response('Could not find %s' % (heard_show), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)

# Handle the CurrentPlayItemInquiry intent.

def alexa_current_playitem_inquiry(slots):
  card_title = "Currently playing item"
  print card_title
  sys.stdout.flush()

  speech_output = 'The current'
  speech_output_append = 'ly playing item is unknown'

  try:
    curitem = kodi.GetActivePlayItem()
  except:
    speech_output = 'There is nothing current'
    speech_output_append = 'ly playing'
  else:
    if curitem is not None:
      if curitem['type'] == 'episode':
        # is a tv show
        speech_output += ' TV show is'
        speech_output_append = ' unknown'
        if curitem['showtitle']:
          speech_output += ' %s,' % (curitem['showtitle'])
          speech_output_append = ''
        if curitem['season']:
          speech_output += ' season %s,' % (curitem['season'])
          speech_output_append = ''
        if curitem['episode']:
          speech_output += ' episode %s,' % (curitem['episode'])
          speech_output_append = ''
        if curitem['title']:
          speech_output += ' %s' % (curitem['title'])
          speech_output_append = ''
      elif curitem['type'] == 'song' or curitem['type'] == 'musicvideo':
        # is a song (music video or audio)
        speech_output += ' song is'
        speech_output_append = ' unknown'
        if curitem['title']:
          speech_output += ' %s,' % (curitem['title'])
          speech_output_append = ''
        if curitem['artist']:
          speech_output += ' by %s,' % (curitem['artist'][0])
          speech_output_append = ''
        if curitem['album']:
          speech_output += ' on the album %s' % (curitem['album'])
          speech_output_append = ''
      elif curitem['type'] == 'movie':
        # is a video
        speech_output += ' movie is'
        speech_output_append = ' unknown'
        if curitem['title']:
          speech_output += ' %s' % (curitem['title'])
          speech_output_append = ''

    return build_alexa_response('%s%s.' % (speech_output, speech_output_append), card_title)

# Pause Kodi
def alexa_play_pause(slots):
  card_title = 'Playing or pausing'
  print card_title
  sys.stdout.flush()

  kodi.PlayPause()
  answer = ""
  return build_alexa_response(answer, card_title)

# Stop Playback
def alexa_stop(slots):
  card_title = 'Stopping playback'
  print card_title
  sys.stdout.flush()

  kodi.Stop()
  answer = "Playback stopped"
  return build_alexa_response(answer, card_title)

# Step Forward
def alexa_step_forward(slots):
  card_title = 'Stepping forward'
  print card_title
  sys.stdout.flush()

  kodi.StepForward()
  answer = ""
  return build_alexa_response(answer, card_title)

# Step Backward
def alexa_step_backward(slots):
  card_title = 'Stepping backward'
  print card_title
  sys.stdout.flush()

  kodi.StepBackward()
  answer = ""
  return build_alexa_response(answer, card_title)

# Big Step Forward
def alexa_big_step_forward(slots):
  card_title = 'Big Step forward'
  print card_title
  sys.stdout.flush()

  kodi.BigStepForward()
  answer = ""
  return build_alexa_response(answer, card_title)

# Big Step Backward
def alexa_big_step_backward(slots):
  card_title = 'Big Step backward'
  print card_title
  sys.stdout.flush()

  kodi.BigStepBackward()
  answer = ""
  return build_alexa_response(answer, card_title)

# Shuffle all music by an artist
def alexa_play_artist(slots):
  heard_artist = str(slots['Artist']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing music by %s' % (heard_artist)
  print card_title
  sys.stdout.flush()

  artists = kodi.GetMusicArtists()
  if 'result' in artists and 'artists' in artists['result']:
    artists_list = artists['result']['artists']
    located = kodi.matchHeard(heard_artist, artists_list, 'artist')

    if located:
      songs_result = kodi.GetArtistSongs(located['artistid'])
      songs = songs_result['result']['songs']

      kodi.Stop()
      kodi.ClearPlaylist()

      songs_array = []

      for song in songs:
        songs_array.append(song['songid'])

      kodi.AddSongsToPlaylist(songs_array)

      kodi.StartPlaylist()
      return build_alexa_response('Playing %s' % (heard_artist), card_title)
    else:
      return build_alexa_response('Could not find %s' % (heard_artist), card_title)
  else:
    return build_alexa_response('Could not find %s' % (heard_artist), card_title)

# Shuffle all recently added songs
def alexa_play_recently_added_songs(slots):
  card_title = 'Playing recently added songs'
  print card_title
  sys.stdout.flush()

  songs_result = kodi.GetRecentlyAddedSongs()
  if songs_result:
    songs = songs_result['result']['songs']

    kodi.Stop()
    kodi.ClearPlaylist()

    songs_array = []

    for song in songs:
      songs_array.append(song['songid'])

    kodi.AddSongsToPlaylist(songs_array)

    kodi.StartPlaylist()
    return build_alexa_response('Playing recently added songs', card_title)
  return build_alexa_response('No recently added songs found', card_title)

def alexa_play_playlist(slots):
  heard_playlist = str(slots['Playlist']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing playlist "%s"' % (heard_playlist)
  print card_title
  sys.stdout.flush()

  playlists = kodi.GetMusicPlaylists()
  if 'result' in playlists and 'files' in playlists['result']:
    playlists_list = playlists['result']['files']
    located = kodi.matchHeard(heard_playlist, playlists_list, 'label')

    if located:
      print 'Located playlist "%s"' % (located['file'])
      sys.stdout.flush()
      kodi.StartPlaylist(located['file'])
      return build_alexa_response('Playing playlist %s' % (heard_playlist), card_title)
    else:
      return build_alexa_response('I Could not find a playlist named %s' % (heard_playlist), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)

def alexa_party_play(slots):
  card_title = 'Party Mode'
  songs = kodi.GetAllSongs()

  if 'result' in songs and 'songs' in songs['result']:
    kodi.Stop()
    kodi.ClearPlaylist()

    songs_array = []

    for song in songs['result']['songs']:
      songs_array.append(song['songid'])

    random.shuffle(songs_array)
    print songs_array

    kodi.AddSongsToPlaylist(songs_array)
    kodi.StartPlaylist()
    return build_alexa_response('Starting party play', card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)

def alexa_start_over(slots):
  card_title = 'Starting current item over'
  print card_title
  sys.stdout.flush()

  kodi.PlayStartOver()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_skip(slots):
  card_title = 'Playing next item'
  print card_title
  sys.stdout.flush()

  kodi.PlaySkip()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_prev(slots):
  card_title = 'Playing previous item'
  print card_title
  sys.stdout.flush()

  kodi.PlayPrev()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_fullscreen(slots):
  card_title = 'Toggling fullscreen'
  print card_title
  sys.stdout.flush()

  kodi.ToggleFullscreen()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_mute(slots):
  card_title = 'Muting or unmuting'
  print card_title
  sys.stdout.flush()

  kodi.ToggleMute()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_subtitles_on(slots):
  card_title = 'Enabling subtitles'
  print card_title
  sys.stdout.flush()

  kodi.SubtitlesOn()
  answer = kodi.GetCurrentSubtitles()
  return build_alexa_response(answer, card_title)

def alexa_subtitles_off(slots):
  card_title = 'Disabling subtitles'
  print card_title
  sys.stdout.flush()

  kodi.SubtitlesOff()
  answer = kodi.GetCurrentSubtitles()
  return build_alexa_response(answer, card_title)

def alexa_subtitles_next(slots):
  card_title = 'Switching to next subtitles'
  print card_title
  sys.stdout.flush()

  kodi.SubtitlesNext()
  answer = kodi.GetCurrentSubtitles()
  return build_alexa_response(answer, card_title)

def alexa_subtitles_previous(slots):
  card_title = 'Switching to previous subtitles'
  print card_title
  sys.stdout.flush()

  kodi.SubtitlesPrevious()
  answer = kodi.GetCurrentSubtitles()
  return build_alexa_response(answer, card_title)

def alexa_audiostream_next(slots):
  card_title = 'Switching to next audio stream'
  print card_title
  sys.stdout.flush()

  kodi.AudioStreamNext()
  answer = kodi.GetCurrentAudioStream()
  return build_alexa_response(answer, card_title)

def alexa_audiostream_previous(slots):
  card_title = 'Switching to previous audio stream'
  print card_title
  sys.stdout.flush()

  kodi.AudioStreamPrevious()
  answer = kodi.GetCurrentAudioStream()
  return build_alexa_response(answer, card_title)

def alexa_player_move_up(slots):
  card_title = 'Player move up'
  print card_title
  sys.stdout.flush()

  kodi.PlayerMoveUp()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_move_down(slots):
  card_title = 'Player move down'
  print card_title
  sys.stdout.flush()

  kodi.PlayerMoveDown()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_move_left(slots):
  card_title = 'Player move left'
  print card_title
  sys.stdout.flush()

  kodi.PlayerMoveLeft()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_move_right(slots):
  card_title = 'Player move right'
  print card_title
  sys.stdout.flush()

  kodi.PlayerMoveRight()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_rotate_clockwise(slots):
  card_title = 'Player rotate clockwise'
  print card_title
  sys.stdout.flush()

  kodi.PlayerRotateClockwise()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_rotate_counterclockwise(slots):
  card_title = 'Player rotate counter clockwise'
  print card_title
  sys.stdout.flush()

  kodi.PlayerRotateCounterClockwise()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_hold(slots):
  card_title = 'Taking screenshot'
  print card_title
  sys.stdout.flush()

  #kodi.Screenshot()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_in(slots):
  card_title = 'Player zoom in'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomIn()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_in_move_up(slots):
  card_title = 'Player zoom in and move up'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomIn()
  kodi.PlayerMoveUp()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_in_move_down(slots):
  card_title = 'Player zoom in and move down'
  sys.stdout.flush()

  kodi.PlayerZoomIn()
  kodi.PlayerMoveDown()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_in_move_left(slots):
  card_title = 'Player zoom in and move left'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomIn()
  kodi.PlayerMoveLeft()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_in_move_right(slots):
  card_title = 'Player zoom in and move right'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomIn()
  kodi.PlayerMoveRight()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_out(slots):
  card_title = 'Player zoom out'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomOut()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_out_move_up(slots):
  card_title = 'Player zoom out and move up'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomOut()
  kodi.PlayerMoveUp()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_out_move_down(slots):
  card_title = 'Player zoom out and move down'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomOut()
  kodi.PlayerMoveDown()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_out_move_left(slots):
  card_title = 'Player zoom out and move left'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomOut()
  kodi.PlayerMoveLeft()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_out_move_right(slots):
  card_title = 'Player zoom out and move right'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoomOut()
  kodi.PlayerMoveRight()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_player_zoom_reset(slots):
  card_title = 'Player zoom normal'
  print card_title
  sys.stdout.flush()

  kodi.PlayerZoom(1)
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_context_menu(slots):
  card_title = 'Navigate: Context Menu'
  print card_title
  sys.stdout.flush()

  kodi.Menu()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_go_home(slots):
  card_title = 'Navigate: Home'
  print card_title
  sys.stdout.flush()

  kodi.Home()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_select(slots):
  card_title = 'Navigate: Select'
  print card_title
  sys.stdout.flush()

  kodi.Select()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_pageup(slots):
  card_title = 'Navigate: Page up'
  print card_title
  sys.stdout.flush()

  kodi.PageUp()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_pagedown(slots):
  card_title = 'Navigate: Page down'
  print card_title
  sys.stdout.flush()

  kodi.PageDown()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_left(slots):
  card_title = 'Navigate: Left'
  print card_title
  sys.stdout.flush()

  kodi.Left()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_right(slots):
  card_title = 'Navigate: Right'
  print card_title
  sys.stdout.flush()

  kodi.Right()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_up(slots):
  card_title = 'Navigate: Up'
  print card_title
  sys.stdout.flush()

  kodi.Up()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_down(slots):
  card_title = 'Navigate: Down'
  print card_title
  sys.stdout.flush()

  kodi.Down()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_back(slots):
  card_title = 'Navigate: Back'
  print card_title
  sys.stdout.flush()

  kodi.Back()
  answer = ""
  return build_alexa_response(answer, card_title)

# Handle the Hibernate intent.

def alexa_hibernate(slots):
  card_title = 'Hibernating'
  print card_title
  sys.stdout.flush()

  kodi.SystemHibernate()
  answer = "Hibernating system"
  return build_alexa_response(answer, card_title)

# Handle the Reboot intent.

def alexa_reboot(slots):
  card_title = 'Rebooting'
  print card_title
  sys.stdout.flush()

  kodi.SystemReboot()
  answer = "Rebooting system"
  return build_alexa_response(answer, card_title)

# Handle the Shutdown intent.

def alexa_shutdown(slots):
  card_title = 'Shutting down'
  print card_title
  sys.stdout.flush()

  kodi.SystemShutdown()
  answer = "Shutting down system"
  return build_alexa_response(answer, card_title)

# Handle the Suspend intent.

def alexa_suspend(slots):
  card_title = 'Suspending'
  print card_title
  sys.stdout.flush()

  kodi.SystemSuspend()
  answer = "Suspending system"
  return build_alexa_response(answer, card_title)

# Handle the EjectMedia intent.

def alexa_ejectmedia(slots):
  card_title = 'Ejecting media'
  print card_title
  sys.stdout.flush()

  kodi.SystemEjectMedia()
  answer = ""
  return build_alexa_response(answer, card_title)

def alexa_clean_video(slots):
  card_title = 'Cleaning video library'
  print card_title
  sys.stdout.flush()

  kodi.UpdateVideo()

  # Use threading to solve the call from returing too late
  c = threading.Thread(target=kodi.CleanVideo)
  c.daemon = True
  c.start()

  # Calling this because for some reason it won't fire until the next command happens?
  kodi.Home()

  answer = "Cleaning video library"
  return build_alexa_response(answer, card_title)

def alexa_update_video(slots):
  card_title = 'Updating video library'
  print card_title
  sys.stdout.flush()

  kodi.UpdateVideo()

  answer = "Updating video library"
  return build_alexa_response(answer, card_title)

def alexa_clean_audio(slots):
  card_title = 'Cleaning audio library'
  print card_title
  sys.stdout.flush()

  kodi.UpdateMusic()

  #Use threading to solve the call from returing too late
  c = threading.Thread(target=kodi.CleanMusic)
  c.daemon = True
  c.start()

  #Calling this because for some reason it won't fire until the next command happens?
  kodi.Home()

  answer = "Cleaning audio library"
  return build_alexa_response(answer, card_title)

def alexa_update_audio(slots):
  card_title = 'Updating audio library'
  print card_title
  sys.stdout.flush()

  kodi.UpdateMusic()

  answer = "Updating audio library"
  return build_alexa_response(answer, card_title)

def alexa_do_search(slots):
  card_title = 'Search'
  heard_search = ''

  if 'value' in slots['Movie']:
    heard_search = str(slots['Movie']['value']).lower().translate(None, string.punctuation)
  elif 'value' in slots['Show']:
    heard_search = str(slots['Show']['value']).lower().translate(None, string.punctuation)
  elif 'value' in slots['Artist']:
    heard_search = str(slots['Artist']['value']).lower().translate(None, string.punctuation)

  if (len(heard_search) > 0):
    answer = 'Searching for %s' % (heard_search)

    kodi.Home()
    kodi.CallKodiSearch(heard_search)

    return build_alexa_response(answer, card_title)
  else:
    return build_alexa_response("Couldn't find anything matching that phrase", card_title)

def alexa_play_random_movie(slots):
  card_title = 'Playing a random movie'
  print card_title
  sys.stdout.flush()

  movies = kodi.GetUnwatchedMovies()
  if not 'movies' in movies['result']:
    # Fall back to all movies if no unwatched available
    movies = kodi.GetMovies()

  if 'result' in movies and 'movies' in movies['result']:
    movies_array = movies['result']['movies']
    random_movie = random.choice(movies_array)

    kodi.ClearVideoPlaylist()
    kodi.PrepMoviePlaylist(random_movie['movieid'])
    kodi.StartVideoPlaylist()

    return build_alexa_response('Playing %s' % (random_movie['label']), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)

def alexa_play_movie(slots):
  heard_movie = str(slots['Movie']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing the movie %s' % (heard_movie)
  print card_title
  sys.stdout.flush()

  movies = kodi.GetMovies()
  if 'result' in movies and 'movies' in movies['result']:
    movies_array = movies['result']['movies']

    located = kodi.matchHeard(heard_movie, movies_array)

    if located:
      kodi.ClearVideoPlaylist()
      kodi.PrepMoviePlaylist(located['movieid'])
      kodi.StartVideoPlaylist()

      return build_alexa_response('Playing %s' % (heard_movie), card_title)
    else:
      return build_alexa_response('Could not find a movie called %s' % (heard_movie), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)

def alexa_play_random_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing a random episode of %s' % (heard_show)
  print card_title
  sys.stdout.flush()

  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']

    located = kodi.matchHeard(heard_show, shows_array)

    if located:
      episodes_result = kodi.GetUnwatchedEpisodesFromShow(located['tvshowid'])

      if not 'episodes' in episodes_result['result']:
        # Fall back to all episodes if no unwatched available
        episodes_result = kodi.GetEpisodesFromShow(located['tvshowid'])

      episodes_array = []

      for episode in episodes_result['result']['episodes']:
        episodes_array.append(episode['episodeid'])

      episode_id = random.choice(episodes_array)
      episode_details = kodi.GetEpisodeDetails(episode_id)['result']['episodedetails']

      kodi.ClearVideoPlaylist()
      kodi.PrepEpisodePlayList(episode_id)
      kodi.StartVideoPlaylist()

      return build_alexa_response('Playing season %d episode %d of %s' % (episode_details['season'], episode_details['episode'], heard_show), card_title)
    else:
      return build_alexa_response('Could not find a show named %s' % (heard_show), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)


def alexa_play_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing an episode of %s' % (heard_show)
  print card_title
  sys.stdout.flush()

  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']

    heard_season = slots['Season']['value']
    heard_episode = slots['Episode']['value']

    located = kodi.matchHeard(heard_show, shows_array)

    if located:
      episode_result = kodi.GetSpecificEpisode(located['tvshowid'], heard_season, heard_episode)

      if episode_result:
        kodi.ClearVideoPlaylist()
        kodi.PrepEpisodePlayList(episode_result)
        kodi.StartVideoPlaylist()

        return build_alexa_response('Playing season %s episode %s of %s' % (heard_season, heard_episode, heard_show), card_title)

      else:
        return build_alexa_response('Could not find season %s episode %s of %s' % (heard_season, heard_episode, heard_show), card_title)
    else:
      return build_alexa_response('Could not find a show named %s' % (heard_show), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)


def alexa_play_next_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing the next unwatched episode of %s' % (heard_show)
  print card_title
  sys.stdout.flush()

  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']

    located = kodi.matchHeard(heard_show, shows_array)

    if located:
      next_episode = kodi.GetNextUnwatchedEpisode(located['tvshowid'])

      if next_episode:
        episode_details = kodi.GetEpisodeDetails(next_episode)['result']['episodedetails']

        kodi.ClearVideoPlaylist()
        kodi.PrepEpisodePlayList(next_episode)
        kodi.StartVideoPlaylist()

        return build_alexa_response('Playing season %d episode %d of %s' % (episode_details['season'], episode_details['episode'], heard_show), card_title)
      else:
        return build_alexa_response('No new episodes for %s' % (heard_show), card_title)
    else:
      return build_alexa_response('Could not find a show named %s' % (heard_show), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)


def alexa_play_newest_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)

  card_title = 'Playing the newest episode of %s' % (heard_show)
  print card_title
  sys.stdout.flush()

  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']

    located = kodi.matchHeard(heard_show, shows_array)

    if located:
      episode = kodi.GetNewestEpisodeFromShow(located['tvshowid'])

      if episode:
        episode_details = kodi.GetEpisodeDetails(episode)['result']['episodedetails']

        kodi.ClearVideoPlaylist()
        kodi.PrepEpisodePlayList(episode)
        kodi.StartVideoPlaylist()

        return build_alexa_response('Playing season %d episode %d of %s' % (episode_details['season'], episode_details['episode'], heard_show), card_title)
      else:
        return build_alexa_response('No new episodes for %s' % (heard_show), card_title)
    else:
      return build_alexa_response('Could not find %s' % (heard_show), card_title)
  else:
    return build_alexa_response('Error parsing results', card_title)


def alexa_continue_show(slots):
  card_title = 'Playing the next unwatched episode of the last show watched'
  print card_title
  sys.stdout.flush()

  last_show_obj = kodi.GetLastWatchedShow()

  try:
    last_show_id = last_show_obj['result']['episodes'][0]['tvshowid']
    next_episode = kodi.GetNextUnwatchedEpisode(last_show_id)

    if next_episode:
      episode_details = kodi.GetEpisodeDetails(next_episode)['result']['episodedetails']

      kodi.ClearVideoPlaylist()
      kodi.PrepEpisodePlayList(next_episode)
      kodi.StartVideoPlaylist()

      return build_alexa_response('Playing season %d episode %d of %s' % (episode_details['season'], episode_details['episode'], last_show_obj['result']['episodes'][0]['showtitle']), card_title)
    else:
      return build_alexa_response('No new episodes for %s' % last_show_obj['result']['episodes'][0]['showtitle'], card_title)
  except:
    return build_alexa_response('Error parsing results', card_title)

# Handle the WhatNewShows intent.

def alexa_what_new_episodes(slots):
  card_title = 'Newly added shows'
  sys.stdout.flush()

  # Lists the shows that have had new episodes added to Kodi in the last 5 days

  # Get the list of unwatched EPISODES from Kodi
  new_episodes = kodi.GetUnwatchedEpisodes()

  # Find out how many EPISODES were recently added and get the names of the SHOWS
  really_new_episodes = [x for x in new_episodes if x['dateadded'] >= datetime.datetime.today() - datetime.timedelta(5)]
  really_new_show_names = list(set([sanitize_show(x['show']) for x in really_new_episodes]))
  num_shows = len(really_new_show_names)

  if num_shows == 0:
    # There's been nothing added to Kodi recently
    answers = [
      "You don't have any new shows to watch.",
      "There are no new shows to watch.",
    ]
    answer = random.choice(answers)
    if random.random() < 0.25:
      comments = [
        " Maybe you should go to the movies.",
        " Maybe you'd like to read a book.",
        " Time to go for a bike ride?",
        " You probably have chores to do anyway.",
      ]
      answer += random.choice(comments)
  elif len(really_new_show_names) == 1:
    # There's only one new show, so provide information about the number of episodes, too.
    count = len(really_new_episodes)
    if count == 1:
      answers = [
        "There is a single new episode of %(show)s." % {'show':really_new_show_names[0]},
        "There is one new episode of %(show)s." % {'show':really_new_show_names[0]},
      ]
    elif count == 2:
      answers = [
        "There are a couple new episodes of %(show)s" % {'show':really_new_show_names[0]},
        "There are two new episodes of %(show)s" % {'show':really_new_show_names[0]},
      ]
    elif count >= 5:
      answers = [
        "There are lots and lots of new episodes of %(show)s" % {'show':really_new_show_names[0]},
        "There are %(count)d new episodes of %(show)s" % {"count":count, "show":really_new_show_names[0]},
      ]
    else:
      answers = [
        "You have a few new episodes of %(show)s" % {'show':really_new_show_names[0]},
        "There are %(count)d new episodes of %(show)s" % {"count":count, "show":really_new_show_names[0]},
      ]
    answer = random.choice(answers)
  else:
    # More than one new show has new episodes ready
    random.shuffle(really_new_show_names)
    show_list = really_new_show_names[0]
    for one_show in really_new_show_names[1:-1]:
      show_list += ", " + one_show
    show_list += ", and " + really_new_show_names[-1]
    answer = "There are new episodes of %(show_list)s." % {"show_list":show_list}
  return build_alexa_response(answer, card_title)

def alexa_watch_pvr_channel(slots):
  heard_pvr_channel = str(slots['Channel']['value']).lower()

  print('Trying to play the PVR channel %s' % (heard_pvr_channel))
  sys.stdout.flush()

  try:
    pvr_channels_by_label = pvr.get_pvr_channels_by_label()
  except IOError:
      return build_alexa_response('Error parsing results.')

  #print(channel['label'] for channel in pvr_channels_by_label)
  located = process.extract(heard_pvr_channel, pvr_channels_by_label.keys(), scorer=fuzz.QRatio, limit=1)
  channel, score = located[0]

  if score > 75:
    kodi.WatchPVRChannel(pvr_channels_by_label[channel.lower()])

    return build_alexa_response('Playing PVR channel %s' % (channel))
  else:
    return build_alexa_response('Could not find a PVR channel called %s' % (heard_pvr_channel))


def alexa_watch_pvr_broadcast(slots):
  heard_pvr_broadcast = str(slots['Broadcast']['value'])
  timeout_seconds = pvr.BROADCAST_SCAN_TIMEOUT

  print('Searching for %s' % (heard_pvr_broadcast))
  sys.stdout.flush()

  try:
    # pvr_broadcasts = pvr.get_pvr_favourite_broadcasts()
    pvr_broadcasts = pvr.get_pvr_broadcasts()
  except IOError:
    return build_alexa_response('Error parsing results.')

  print('start search')
  # print(pvr_broadcasts)
  best_candidate = None
  stop_time = datetime.datetime.utcnow() + datetime.timedelta(0, timeout_seconds)
  for channelid, broadcasts in pvr_broadcasts.items():
    if datetime.datetime.utcnow() >= stop_time:
      print('timed out after %n seconds' % (timeout_seconds))
      break

    #print(channelid)
    #print(best_candidate)

    candidate = None
    now = datetime.datetime.utcnow()
    for broadcast in broadcasts:
      # all dates in the response appear to be UTC
      endtime = datetime.datetime.strptime(broadcast['endtime'], "%Y-%m-%d %H:%M:%S", )
      if endtime < now:
        continue
      if best_candidate and best_candidate['score'] == 100:
        if endtime > best_candidate['endtime']:
          #no point looking further ahead when we already have a perfect match that ends earlier
          break
        #we already have a perfect match so now we don't need to use the expensive fuzzywuzzy search
        score = 100 if best_candidate['label'] == broadcast['label'] else 0
        #print('%s score %d' % (broadcast['label'], score))
      else:
        score = fuzz.QRatio(heard_pvr_broadcast, broadcast['label'])
        if score < 75:
          continue
      if candidate is None or score > candidate['score']:
        candidate = {'channel': channelid, 'score': score, 'label': broadcast['label'], 'endtime': endtime}
      if score == 100:
        break

    if candidate:
      if best_candidate is None or (
          candidate['score'] > best_candidate['score'] or
                (candidate['endtime'] < best_candidate['endtime' ] and candidate['score'] == best_candidate['score'])):
        #print(candidate)
        best_candidate = candidate

  print('end search')
  if best_candidate:
    print(best_candidate)
    kodi.WatchPVRChannel(best_candidate['channel'])

    return build_alexa_response('Playing %s' % (best_candidate['label']))
  else:
    return build_alexa_response('Could not find a PVR broadcast called %s' % (heard_pvr_broadcast))

# What should the Echo say when you just open your app instead of invoking an intent?

def prepare_help_message():
  help = "You can ask me whether there are any new shows, to play a movie, tv show, or artist, or control playback of media."
  card_title = "Help"
  return build_alexa_response(help, card_title)


# This maps the Intent names to the functions that provide the corresponding Alexa response.

INTENTS = [
  ['CheckNewShows', alexa_check_new_episodes],
  ['NewShowInquiry', alexa_new_show_inquiry],
  ['CurrentPlayItemInquiry', alexa_current_playitem_inquiry],
  ['WhatNewShows', alexa_what_new_episodes],
  ['PlayPause', alexa_play_pause],
  ['StepForward', alexa_step_forward],
  ['BigStepForward', alexa_big_step_forward],
  ['StepBackward', alexa_step_backward],
  ['BigStepBackward', alexa_big_step_backward],
  ['Stop', alexa_stop],
  ['ListenToArtist', alexa_play_artist],
  ['ListenToPlaylist', alexa_play_playlist],
  ['ListenToPlaylistRecent', alexa_play_recently_added_songs],
  ['Skip', alexa_skip],
  ['Prev', alexa_prev],
  ['StartOver', alexa_start_over],
  ['PlayRandomEpisode', alexa_play_random_episode],
  ['PlayRandomMovie', alexa_play_random_movie],
  ['PlayMovie', alexa_play_movie],
  ['Home', alexa_go_home],
  ['Back', alexa_back],
  ['Up', alexa_up],
  ['Down', alexa_down],
  ['Right', alexa_right],
  ['Left', alexa_left],
  ['Select', alexa_select],
  ['Menu', alexa_context_menu],
  ['PageUp', alexa_pageup],
  ['PageDown', alexa_pagedown],
  ['Fullscreen', alexa_fullscreen],
  ['Mute', alexa_mute],
  ['SubtitlesOn', alexa_subtitles_on],
  ['SubtitlesOff', alexa_subtitles_off],
  ['SubtitlesNext', alexa_subtitles_next],
  ['SubtitlesPrevious', alexa_subtitles_previous],
  ['AudioStreamNext', alexa_audiostream_next],
  ['AudioStreamPrevious', alexa_audiostream_previous],
  ['PlayerMoveUp', alexa_player_move_up],
  ['PlayerMoveDown', alexa_player_move_down],
  ['PlayerMoveLeft', alexa_player_move_left],
  ['PlayerMoveRight', alexa_player_move_right],
  ['PlayerRotateClockwise', alexa_player_rotate_clockwise],
  ['PlayerRotateCounterClockwise', alexa_player_rotate_counterclockwise],
  ['PlayerZoomHold', alexa_player_zoom_hold],
  ['PlayerZoomIn', alexa_player_zoom_in],
  ['PlayerZoomInMoveUp', alexa_player_zoom_in_move_up],
  ['PlayerZoomInMoveDown', alexa_player_zoom_in_move_down],
  ['PlayerZoomInMoveLeft', alexa_player_zoom_in_move_left],
  ['PlayerZoomInMoveRight', alexa_player_zoom_in_move_right],
  ['PlayerZoomOut', alexa_player_zoom_out],
  ['PlayerZoomOutMoveUp', alexa_player_zoom_out_move_up],
  ['PlayerZoomOutMoveDown', alexa_player_zoom_out_move_down],
  ['PlayerZoomOutMoveLeft', alexa_player_zoom_out_move_left],
  ['PlayerZoomOutMoveRight', alexa_player_zoom_out_move_right],
  ['PlayerZoomReset', alexa_player_zoom_reset],
  ['PlayEpisode', alexa_play_episode],
  ['PlayNextEpisode', alexa_play_next_episode],
  ['ContinueShow', alexa_continue_show],
  ['CleanVideo', alexa_clean_video],
  ['UpdateVideo', alexa_update_video],
  ['CleanAudio', alexa_clean_audio],
  ['UpdateAudio', alexa_update_audio],
  ['PlayLatestEpisode', alexa_play_newest_episode],
  ['PartyMode', alexa_party_play],
  ['DoSearch', alexa_do_search],
  ['Hibernate', alexa_hibernate],
  ['Reboot', alexa_reboot],
  ['Shutdown', alexa_shutdown],
  ['Suspend', alexa_suspend],
  ['EjectMedia', alexa_ejectmedia],
  ['WatchPVRChannel', alexa_watch_pvr_channel],
  ['WatchPVRBroadcast', alexa_watch_pvr_broadcast]
]


def on_session_started(session_started_request, session):
  print("on_session_started: requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])

def on_intent(intent_request, session):
  print("on_intent: requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

  intent = intent_request['intent']
  intent_name = intent_request['intent']['name']
  intent_slots = intent_request['intent'].get('slots',{})

  # Dispatch to your skill's intent handlers
  response = None

  print('Requested intent: %s' % (intent_name))
  sys.stdout.flush()

  # Run the function associated with the intent
  for one_intent in INTENTS:
    if intent_name == one_intent[0]:
      return one_intent[1](intent_slots)
      break
  if not response:
    return prepare_help_message()

def verify_application_id(candidate):
  if env('SKILL_APPID'):
    try:
      print "Verifying application ID..."
      if candidate not in env('SKILL_APPID'):
        raise ValueError("Application ID verification failed")
    except ValueError as e:
      print e.args[0]
      raise


# The main entry point for lambda
def lambda_handler(event, context):
  appid = event['session']['application']['applicationId']
  print("lambda_handler: applicationId=" + appid)

  setup_env()

  # Verify the application ID is what the user expects
  verify_application_id(appid)

  if event['session']['new']:
    on_session_started({'requestId': event['request']['requestId']}, event['session'])

  if event['request']['type'] == "LaunchRequest":
    return prepare_help_message()
  elif event['request']['type'] == "IntentRequest":
    return on_intent(event['request'], event['session'])
  else:
    return build_alexa_response("I received an unexpected request type.")


def wsgi_handler(environ, start_response):
  # Alexa requests come as POST messages with a request body
  try:
    length = int(environ.get('CONTENT_LENGTH', '0'))
  except ValueError:
    length = 0

  if length > 0:
    # Get the request body and parse out the Alexa JSON request
    body = environ['wsgi.input'].read(length)
    alexa_msg = json.loads(body)
    alexa_session = alexa_msg['session']
    alexa_request = alexa_msg['request']

    appid = alexa_msg['session']['application']['applicationId']
    print("wsgi_handler: applicationId=" + appid)

    # Verify the request is coming from Amazon and includes a valid signature.
    try:
      if env('SKILL_VERIFY_CERT'):
        print "Verifying certificate is valid..."
        cert_url = environ['HTTP_SIGNATURECERTCHAINURL']
        signature = environ['HTTP_SIGNATURE']
        cert = verifier.load_certificate(cert_url)
        verifier.verify_signature(cert, signature, body)
        timestamp = aniso8601.parse_datetime(alexa_request['timestamp'])
        verifier.verify_timestamp(timestamp)
    except verifier.VerificationError as e:
      print e.args[0]
      raise

    # Verify the application ID is what the user expects
    verify_application_id(appid)

    if alexa_session['new']:
      on_session_started({'requestId': alexa_request['requestId']}, alexa_session)

    if alexa_request['type'] == 'LaunchRequest':
      # This is the type when you just say "Open <app>"
      response = prepare_help_message()

    elif alexa_request['type'] == 'IntentRequest':
      response = on_intent(alexa_request, alexa_session)

    else:
      response = build_alexa_response("I received an unexpected request type.")

    start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(json.dumps(response))))])
    return [json.dumps(response)]
  else:
    # This should never happen with a real Echo request but could happen
    # if your URL is accessed by a browser or otherwise.
    start_response('502 No content', [])
    return ['']

# Map the URL to the WSGI function that should handle it.
WSGI_HANDLERS = [
  ['/', wsgi_handler],
  ['', wsgi_handler],
]

# The main entry point for WSGI scripts
def application(environ, start_response):
  setup_env()

  # Execute the handler that matches the URL
  for h in WSGI_HANDLERS:
    if environ['PATH_INFO'] == h[0]:
      output = h[1](environ, start_response)
      return output

  # If we don't have a handler for the URL, return a 404 error
  # page with diagnostic info. The details should be left blank
  # in a real production environment.

  details = ''
  if False:  # Change to False for production!
    for k in sorted(environ.keys()):
      details += '%s = %s<br/>\n' % (k, environ[k])
  output = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL %(url)s was not found on this server.</p>
<hr/>
%(details)s
<hr/>
<address>%(address)s</address>
</body></html>
""" % {'url':environ['PATH_INFO'], 'address':environ['SERVER_SIGNATURE'], 'details':details}
  start_response('404 Not Found', [('Content-type', 'text/html')])
  return [output]
