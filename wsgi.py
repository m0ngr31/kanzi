#!/usr/bin/python
import os

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

# Load the kodi.py file from the same directory where this wsgi file is located
sys.path += [os.path.dirname(__file__)]
import kodi

# This utility function constructs the required JSON for a full Alexa Skills Kit response

RE_SHOW_WITH_PARAM = re.compile(r"(.*) \([^)]+\)$")

def sanitize_show(show_name):
  m = RE_SHOW_WITH_PARAM.match(show_name)
  if m:
    return m.group(1)
  return show_name

def build_alexa_response(speech = None, session_attrs = None, card = None, reprompt = None, end_session = True):
  reply = {"version" : "1.0"}
  if session_attrs:
    reply['sessionAttributes'] = session_attrs
  response = {}
  if speech:
    response['outputSpeech'] = {'type':'PlainText', 'text':speech}
  if card:
    response['card'] = card
  if reprompt:
    response['reprompt'] = {'outputSpeech':{'type':'PlainText','text':reprompt}}
  response['shouldEndSession'] = end_session
  reply['response'] = response
  return json.dumps(reply)


# Handle the CheckNewShows intent

def alexa_check_new_episodes(slots):
  # Responds to the question, "Are there any new shows to watch?"

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
  return build_alexa_response(answer)


# Handle the NewShowInquiry intent.

def alexa_new_show_inquiry(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)
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
          return build_alexa_response("There is one unseen episode of %(real_show)s." % {'real_show': heard_show})
        else:
          return build_alexa_response("There are %(num)d episodes of  %(real_show)s." % {'real_show': heard_show, 'num': num_of_unwatched})
      
      else:
        return build_alexa_response("There are no unseen episodes of %(real_show)s." % {'real_show': heard_show})
    else:
      return build_alexa_response('Could not find %s' % (heard_show))
  else:
    return build_alexa_response('Could not find %s' % (heard_show))

#Pause Kodi
def alexa_play_pause(slots):
  kodi.PlayPause()
  answer = ""
  return build_alexa_response(answer)

# Stop Playback
def alexa_stop(slots):
  kodi.Stop()
  answer = "Playback Stopped"
  return build_alexa_response(answer)

# Suffle all music by an artist
def alexa_play_artist(slots):
  heard_artist = str(slots['Artist']['value']).lower().translate(None, string.punctuation)
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
      return build_alexa_response('Playing %s' % (heard_artist))
    else:
      return build_alexa_response('Could not find %s' % (heard_artist))
  else:
    return build_alexa_response('Could not find %s' % (heard_artist))
  
def alexa_start_over(slots):
  kodi.PlayStartOver()
  return build_alexa_response('Starting over')
  
def alexa_skip(slots):
  kodi.PlaySkip()
  return build_alexa_response('Skipping item')
  
def alexa_pageup(slots):
  kodi.PageUp()
  return build_alexa_response('')
  
def alexa_pagedown(slots):
  kodi.PageDown()
  return build_alexa_response('')
  
def alexa_context_menu(slots):
  kodi.Menu()
  return build_alexa_response('Opening menu')
  
def alexa_go_home(slots):
  kodi.Home()
  return build_alexa_response('Going home')
  
def alexa_select(slots):
  kodi.Select()
  return build_alexa_response('')
  
def alexa_left(slots):
  kodi.Left()
  return build_alexa_response('')
  
def alexa_right(slots):
  kodi.Right()
  return build_alexa_response('')
  
def alexa_up(slots):
  kodi.Up()
  return build_alexa_response('')
  
def alexa_down(slots):
  kodi.Down()
  return build_alexa_response('')
  
def alexa_back(slots):
  kodi.Back()
  return build_alexa_response('')

def alexa_prev(slots):
  kodi.PlayPrev()
  return build_alexa_response('Playing previous item')
  
def alexa_clean_video(slots):
  kodi.CleanVideo()
  kodi.UpdateVideo()
  return build_alexa_response('Cleaning and updating video library')

def alexa_update_video(slots):
  kodi.UpdateVideo()
  return build_alexa_response('Updating video library')

def alexa_clean_audio(slots):
  kodi.CleanMusic()
  kodi.UpdateMusic()
  return build_alexa_response('Cleaning and updating audio library')
  
def alexa_update_audio(slots):
  kodi.UpdateMusic()
  return build_alexa_response('Updating audio library')

def alexa_pick_random_movie(slots):
  movies_response = kodi.GetUnwatchedMovies()
  if 'result' in movies_response and 'movies' in movies_response['result']:
    movies = movies_response['result']['movies']
    random_movie = random.choice(movies)

    kodi.ClearVideoPlaylist()
    kodi.PrepMoviePlaylist(random_movie['movieid'])
    kodi.StartVideoPlaylist()
    
    return build_alexa_response('Playing %s' % (random_movie['label']))
  else:
    return build_alexa_response("Couldn't find any movies")
  
def alexa_play_movie(slots):
  heard_movie = str(slots['Movie']['value']).lower().translate(None, string.punctuation)
  movies_response = kodi.GetMovies()
  if 'result' in movies_response and 'movies' in movies_response['result']:
    movies = movies_response['result']['movies']
    
    located = kodi.matchHeard(heard_movie, movies)
    
    if located:
      kodi.ClearVideoPlaylist()
      kodi.PrepMoviePlaylist(located['movieid'])
      kodi.StartVideoPlaylist()
      
      return build_alexa_response('Playing %s' % (heard_movie))
    else:
      return build_alexa_response('Could not find a movie called %s' % (heard_movie))
  else:
    return build_alexa_response('Could not find a movie called %s' % (heard_movie))
  
def alexa_pick_random_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)
  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']
    
    located = kodi.matchHeard(heard_show, shows_array)
    
    if located:
      episodes_result = kodi.GetUnwatchedEpisodesFromShow(located['tvshowid'])
      
      if not 'episodes' in episodes_result['result']:
        episodes_result = kodi.GetEpisodesFromShow(located['tvshowid'])

      episodes_array = []

      for episode in episodes_result['result']['episodes']:
        episodes_array.append(episode['episodeid'])

      kodi.ClearVideoPlaylist()
      kodi.PrepEpisodePlayList(random.choice(episodes_array))

      kodi.StartVideoPlaylist()
      
      return build_alexa_response('Playing a random episode of %s' % (heard_show))
    else:
      return build_alexa_response('Could not find %s' % (heard_show))
  else:
    return build_alexa_response('Could not find %s' % (heard_show))

  
def alexa_play_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)
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
        
        return build_alexa_response('Playing season %s episode %s of %s' % (heard_season, heard_episode, heard_show))
        
      else:
        return build_alexa_response('Could not find season %s episode %s of %s' % (heard_season, heard_episode, heard_show))
    else:
      return build_alexa_response('Could not find %s' % (heard_show))
  else:
    return build_alexa_response('Could not find %s' % (heard_show))
    

def alexa_play_next_episode(slots):
  heard_show = str(slots['Show']['value']).lower().translate(None, string.punctuation)
  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']
    
    located = kodi.matchHeard(heard_show, shows_array)
    
    if located:
      next_episode = kodi.GetNextUnwatchedEpisode(located['tvshowid'])
      
      if next_episode:
        kodi.ClearVideoPlaylist()
        kodi.PrepEpisodePlayList(next_episode)

        kodi.StartVideoPlaylist()
        return build_alexa_response('Playing next episode of %s' % (heard_show))
      else:
        return build_alexa_response('No new episodes for %s' % (heard_show))      
    else:
      return build_alexa_response('Could not find %s' % (heard_show))
  else:
    return build_alexa_response('Could not find %s' % (heard_show))
    

def alexa_play_newest_episode(slots):
  heard_show =  str(slots['Show']['value']).lower().translate(None, string.punctuation)
  shows = kodi.GetTvShows()
  if 'result' in shows and 'tvshows' in shows['result']:
    shows_array = shows['result']['tvshows']
    
    located = kodi.matchHeard(heard_show, shows_array)
    
    if located:
      episode_result = kodi.GetNewestEpisodeFromShow(located['tvshowid'])

      if episode_result:
        kodi.ClearVideoPlaylist()
        kodi.PrepEpisodePlayList(episode_result)
        kodi.StartVideoPlaylist()
        
        return build_alexa_response('Playing lastest episode of %s' % (heard_show))
        
      else:
        return build_alexa_response('Could not find newest episode of %s' % (heard_show))
    else:
      return build_alexa_response('Could not find %s' % (heard_show))
  else:
    return build_alexa_response('Could not find %s' % (heard_show))


def alexa_continue_show(slots):
  last_show_obj = kodi.GetLastWatchedShow()
  
  try:
    last_show_id = last_show_obj['result']['episodes'][0]['tvshowid']
    next_episode = kodi.GetNextUnwatchedEpisode(last_show_id)
    
    if next_episode:
      kodi.ClearVideoPlaylist()
      kodi.PrepEpisodePlayList(next_episode)

      kodi.StartVideoPlaylist()
      return build_alexa_response('Playing next episode')
    else:
      return build_alexa_response('No new episodes') 

  except:
    return build_alexa_response('Could not continue show')

# Handle the WhatNewShows intent.

def alexa_what_new_episodes(slots):
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
  return build_alexa_response(answer)


# What should the Echo say when you just open your app instead of invoking an intent?

def prepare_help_message():
  help = "You can ask me whether there are any new shows, to play a movie, tv show, or artist, or control playback of media."
  return build_alexa_response(help)


# This maps the Intent names to the functions that provide the corresponding Alexa response.

INTENTS = [
  ['CheckNewShows', alexa_check_new_episodes],
  ['NewShowInquiry', alexa_new_show_inquiry],
  ['WhatNewShows', alexa_what_new_episodes],
  ['PlayPause', alexa_play_pause],
  ['Stop', alexa_stop],
  ['ListenToArtist', alexa_play_artist],
  ['Skip', alexa_skip],
  ['Prev', alexa_prev],
  ['StartOver', alexa_start_over],
  ['PlayRandomEpisode', alexa_pick_random_episode],
  ['PlayRandomMovie', alexa_pick_random_movie],
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
  ['PlayEpisode', alexa_play_episode],
  ['PlayNextEpisode', alexa_play_next_episode],
  ['ContinueShow', alexa_continue_show],
  ['CleanVideo', alexa_clean_video],
  ['UpdateVideo', alexa_update_video],
  ['CleanAudio', alexa_clean_audio],
  ['UpdateAudio', alexa_update_audio],
  ['PlayLatestEpisode', alexa_play_newest_episode]
]


# Handle the requests that arrive from the Alexa Skills Kit when your app
# is invoked.

def do_alexa(environ, start_response):
  # Alexa requests come as POST messages with a request body
  try:
    length = int(environ.get('CONTENT_LENGTH', '0'))
  except ValueError:
    length = 0

  if length > 0:
    # Get the request body and parse out the Alexa JSON request
    body = environ['wsgi.input'].read(length)
    alexa_msg = json.loads(body)
    alexa_request = alexa_msg['request']

    if alexa_request['type'] == 'LaunchRequest':
      # This is the type when you just say "Open <app>"
      response = prepare_help_message()

    elif alexa_request['type'] == 'IntentRequest':
      # Get the intent being invoked and any slot values sent with it
      intent_name = alexa_request['intent']['name']
      intent_slots = alexa_request['intent'].get('slots', {})
      response = None

      # Run the function associated with the intent
      for one_intent in INTENTS:
        if intent_name == one_intent[0]:
          response = one_intent[1](intent_slots)
          break
      if not response:
        # This should not happen if your Intent Schema and your INTENTS list above are in sync.
        response = prepare_help_message()
    else:
      response = build_alexa_response("I received an unexpected request type.")
    start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(response)))])
    return [response]
  else:
    # This should never happen with a real Echo request but could happen
    # if your URL is accessed by a browser or otherwise.
    start_response('502 No content', [])
    return ['']


# Map the URL to the WSGI function that should handle it.

HANDLERS = [
  ['/', do_alexa],
  ['', do_alexa],
]


# The main entry point for WSGI scripts

def application(environ, start_response):
  # Execute the handler that matches the URL
  for h in HANDLERS:
    if environ['PATH_INFO'] == h[0]:
      output = h[1](environ, start_response)
      return output

  # If we don't have a handler for the URL, return a 404 error
  # page with diagnostic info. The details should be left blank
  # in a real production environment.

  details = ''
  if False:  # Change to False for productioN!
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