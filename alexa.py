#!/usr/bin/python

# For a complete discussion, see http://forum.kodi.tv/showthread.php?tid=254502

import datetime
import pytz
import random
import string
import sys
import time
import os
import re
import codecs
import logging
from flask import Flask, json, render_template
from functools import wraps
from flask_ask import Ask, session, question, statement, audio, request, context
from shutil import copyfile
from kodi_voice import KodiConfigParser, Kodi


app = Flask(__name__)

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

LOGLEVEL = config.get('global', 'loglevel')
LOGSENSITIVE = config.getboolean('global', 'logsensitive')
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('kodi_alexa.' + __name__)
log.setLevel(LOGLEVEL)
kodi_voice_log = logging.getLogger('kodi_voice')
kodi_voice_log.setLevel(LOGLEVEL)
kodi_voice_log.propagate = True
if LOGSENSITIVE:
  requests_log = logging.getLogger('requests.packages.urllib3')
  requests_log.setLevel(LOGLEVEL)
  requests_log.propagate = True

SKILL_ID = config.get('alexa', 'skill_id')
if SKILL_ID and SKILL_ID != 'None' and not os.getenv('MEDIA_CENTER_SKILL_ID'):
  app.config['ASK_APPLICATION_ID'] = SKILL_ID
elif os.getenv('MEDIA_CENTER_SKILL_ID'):
  app.config['ASK_APPLICATION_ID'] = os.getenv('MEDIA_CENTER_SKILL_ID')

LANGUAGE = config.get('global', 'language')
if LANGUAGE == 'de':
  TEMPLATE_FILE = "templates.de.yaml"
elif LANGUAGE == 'fr':
  TEMPLATE_FILE = "templates.fr.yaml"  
elif LANGUAGE == 'es':
  TEMPLATE_FILE = "templates.es.yaml"
elif LANGUAGE == 'it':
  TEMPLATE_FILE = "templates.it.yaml"
else:
  LANGUAGE = 'en'
  TEMPLATE_FILE = "templates.en.yaml"

# According to this: https://alexatutorial.com/flask-ask/configuration.html
# Timestamp based verification shouldn't be used in production. Use at own risk
# app.config['ASK_VERIFY_TIMESTAMP_DEBUG'] = True

# Needs to be instanced after app is configured
ask = Ask(app, "/", None, path=TEMPLATE_FILE)


# Direct lambda handler
def lambda_handler(event, _context):
  return ask.run_aws_lambda(event)


# Decorator to check your config for basic info and if your account is linked (when using the hosted skill)
def preflight_check(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if os.getenv('MEDIA_CENTER_URL') and not session.get('user', {}).get('accessToken'):
      response_text = render_template('not_logged_in').encode('utf-8')
      return statement(response_text).link_account_card()

    kodi = Kodi(config, context)

    if kodi.config_error:
      if os.getenv('MEDIA_CENTER_URL'):
        response_text = render_template('hosted_config_missing').encode('utf-8')
      else:
        response_text = render_template('config_missing').encode('utf-8')

      card_title = render_template('card_config_missing').encode('utf-8')
      return statement(response_text).simple_card(card_title, response_text)

    # Since we're not getting any of the actual args passed in, we have to create them here
    slots = request.get('intent', {}).get('slots', {})
    for key, value in slots.iteritems():
      kwargs.update({key: value.get('value')})
    kwargs.update({'kodi': kodi})

    return f(*args, **kwargs)
  return decorated_function

# Start of intent methods

# Handle the CurrentPlayItemInquiry intent.
@ask.intent('CurrentPlayItemInquiry')
@preflight_check
def alexa_current_playitem_inquiry(kodi):
  card_title = render_template('current_playing_item').encode('utf-8')
  log.info(card_title)

  response_text = render_template('nothing_playing')

  curitem = kodi.GetActivePlayItem()
  if curitem:
    response_text = render_template('unknown_playing')

    if curitem['type'] == 'episode':
      # is a tv show
      if curitem['showtitle']:
        response_text = render_template('current_show_is')
        response_text += u' '
        response_text += curitem['showtitle']
        if curitem['season']:
          response_text += u', %s %s' % (render_template('season'), curitem['season'])
        if curitem['episode']:
          response_text += u', %s %s' % (render_template('episode'), curitem['episode'])
        if curitem['title']:
          response_text += u', '
          response_text += curitem['title']
    elif curitem['type'] == 'song' or curitem['type'] == 'musicvideo':
      # is a song (music video or audio)
      if curitem['title']:
        response_text = render_template('current_song_is')
        response_text += u' '
        response_text += curitem['title']
        if curitem['artist']:
          response_text += u' ' + render_template('by') + u' '
          response_text += curitem['artist'][0]
        if curitem['album']:
          response_text += u', '
          response_text += render_template('on_the_album')
          response_text += u' '
          response_text += curitem['album']
    elif curitem['type'] == 'movie':
      # is a video
      if curitem['title']:
        response_text = render_template('current_movie_is')
        response_text += u' '
        response_text += curitem['title']

  response_text = response_text.encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the CurrentPlayItemTimeRemaining intent.
@ask.intent('CurrentPlayItemTimeRemaining')
@preflight_check
def alexa_current_playitem_time_remaining(kodi):
  card_title = render_template('time_left_playing').encode('utf-8')
  log.info(card_title)

  response_text = render_template('nothing_playing').encode('utf-8')

  status = kodi.GetPlayerStatus()
  if status['state'] is not 'stop':
    minsleft = status['total_mins'] - status['time_mins']
    if minsleft == 0:
      response_text = render_template('remaining_close').encode('utf-8')
    elif minsleft == 1:
      response_text = render_template('remaining_min').encode('utf-8')
    elif minsleft > 1:
      response_text = render_template('remaining_mins', minutes=minsleft).encode('utf-8')
      tz = config.get(kodi.dev_cfg_section, 'timezone')
      if minsleft > 9 and tz and tz != 'None':
        utctime = datetime.datetime.now(pytz.utc)
        loctime = utctime.astimezone(pytz.timezone(tz))
        endtime = loctime + datetime.timedelta(minutes=minsleft)
        response_text += render_template('remaining_time', end_time=endtime.strftime('%I:%M')).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def alexa_play_pause(kodi):
  card_title = render_template('play_pause').encode('utf-8')
  log.info(card_title)

  kodi.PlayerPlayPause()
  return statement('').simple_card(card_title, '')


# Handle the AMAZON.PauseIntent intent.
@ask.intent('AMAZON.PauseIntent')
@preflight_check
def alexa_pause(kodi):
  return alexa_play_pause(kodi)


# Handle the AMAZON.ResumeIntent intent.
@ask.intent('AMAZON.ResumeIntent')
@preflight_check
def alexa_resume(kodi):
  return alexa_play_pause(kodi)


def alexa_stop_cancel(kodi):
  if session.new:
    card_title = render_template('stopping').encode('utf-8')
    log.info(card_title)

    kodi.PlayerStop()
    response_text = render_template('playback_stopped').encode('utf-8')
    return statement(response_text).simple_card(card_title, response_text)
  else:
    return statement('')


# Handle the AMAZON.StopIntent intent.
@ask.intent('AMAZON.StopIntent')
@preflight_check
def alexa_stop(kodi):
  return alexa_stop_cancel(kodi)


# Handle the AMAZON.CancelIntent intent.
@ask.intent('AMAZON.CancelIntent')
@preflight_check
def alexa_cancel(kodi):
  return alexa_stop_cancel(kodi)


# Handle the AMAZON.NoIntent intent.
@ask.intent('AMAZON.NoIntent')
@preflight_check
def alexa_no(kodi):
  if 'play_media_generic_type' in session.attributes:
    generic_type = session.attributes['play_media_generic_type']
    if generic_type == 'video':
      item = kodi.GetRecommendedVideoItem()
    else:
      item = kodi.GetRecommendedAudioItem()
    return alexa_recommend_item(kodi, item, generic_type)
  elif 'play_media_type' in session.attributes:
    genre = None
    if 'play_media_genre' in session.attributes:
      genre = session.attributes['play_media_genre']
    item = kodi.GetRecommendedItem(session.attributes['play_media_type'] + 's', genre)
    return alexa_recommend_item(kodi, item)

  return alexa_stop_cancel(kodi)


# Handle the AMAZON.YesIntent intent.
@ask.intent('AMAZON.YesIntent')
@preflight_check
def alexa_yes(kodi):
  card_title = None

  if 'shutting_down' in session.attributes:
    quit = config.get(kodi.dev_cfg_section, 'shutdown')
    if quit and quit == 'quit':
      card_title = render_template('quitting').encode('utf-8')
      kodi.ApplicationQuit()
    else:
      card_title = render_template('shutting_down').encode('utf-8')
      kodi.SystemShutdown()
  elif 'rebooting' in session.attributes:
    card_title = render_template('rebooting').encode('utf-8')
    kodi.SystemReboot()
  elif 'hibernating' in session.attributes:
    card_title = render_template('hibernating').encode('utf-8')
    kodi.SystemHibernate()
  elif 'suspending' in session.attributes:
    card_title = render_template('suspending_system').encode('utf-8')
    kodi.SystemSuspend()

  if 'play_media_type' in session.attributes:
    media_type = session.attributes['play_media_type']
    media_id = session.attributes['play_media_id']
    if media_type == 'movie':
      kodi.PlayMovie(media_id)
    elif media_type == 'tvshow':
      # Try the next unwatched episode first
      episode_id = kodi.GetNextUnwatchedEpisode(media_id)
      if not episode_id:
        # All episodes already watched, so just play a random episode
        episodes_result = kodi.GetEpisodesFromShow(media_id)
        for episode in episodes_result['result']['episodes']:
          episodes_array.append(episode['episodeid'])
        episode_id = random.choice(episodes_array)
      kodi.PlayEpisode(episode_id)
    elif media_type == 'episode':
      kodi.PlayEpisode(media_id)
    elif media_type == 'musicvideo':
      kodi.PlayMusicVideo(media_id)
    elif media_type == 'artist':
      songs_result = kodi.GetArtistSongs(media_id)
      songs = songs_result['result']['songs']
      songs_array = []
      for song in songs:
        songs_array.append(song['songid'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
    elif media_type == 'album':
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(media_id)
      kodi.StartAudioPlaylist()
    elif media_type == 'song':
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongToPlaylist(media_id)
      kodi.StartAudioPlaylist()
    return statement(render_template('okay').encode('utf-8'))

  if card_title:
    log.info(card_title)
    return statement(card_title).simple_card(card_title, "")
  else:
    return statement('')


def duration_in_seconds(duration_str):
  if duration_str[0] != 'P':
    raise ValueError('Not an ISO 8601 Duration string')

  seconds = 0
  # split by the 'T'
  for i, item in enumerate(duration_str.split('T')):
    for number, unit in re.findall('(?P<number>\d+)(?P<period>S|M|H|D|W|Y)', item):
      number = int(number)
      this = 0
      if unit == 'Y':
        this = number * 31557600 # 365.25
      elif unit == 'W':
        this = number * 604800
      elif unit == 'D':
        this = number * 86400
      elif unit == 'H':
        this = number * 3600
      elif unit == 'M':
        # ambiguity alleviated with index i
        if i == 0:
          this = number * 2678400 # assume 30 days
        else:
          this = number * 60
      elif unit == 'S':
        this = number
      seconds = seconds + this
  return seconds


# Handle the PlayerSeekForward intent.
@ask.intent('PlayerSeekForward')
@preflight_check
def alexa_player_seek_forward(kodi, ForwardDur):
  card_title = render_template('step_forward').encode('utf-8')
  log.info(card_title)

  seek_sec = duration_in_seconds(ForwardDur)

  card_body = 'Stepping forward by %d seconds' % (seek_sec)
  log.info(card_body)

  kodi.PlayerSeek(seek_sec)
  return statement('').simple_card(card_title, card_body)


# Handle the PlayerSeekBackward intent.
@ask.intent('PlayerSeekBackward')
@preflight_check
def alexa_player_seek_backward(kodi, BackwardDur):
  card_title = render_template('step_backward').encode('utf-8')
  log.info(card_title)

  seek_sec = duration_in_seconds(BackwardDur)

  card_body = 'Stepping backward by %d seconds' % (seek_sec)
  log.info(card_body)

  kodi.PlayerSeek(-seek_sec)
  return statement('').simple_card(card_title, card_body)


# Handle the PlayerSeekSmallForward intent.
@ask.intent('PlayerSeekSmallForward')
@preflight_check
def alexa_player_seek_smallforward(kodi):
  card_title = render_template('step_forward').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSeekSmallForward()
  return statement('').simple_card(card_title, '')


# Handle the PlayerSeekSmallBackward intent.
@ask.intent('PlayerSeekSmallBackward')
@preflight_check
def alexa_player_seek_smallbackward(kodi):
  card_title = render_template('step_backward').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSeekSmallBackward()
  return statement('').simple_card(card_title, '')


# Handle the PlayerSeekBigForward intent.
@ask.intent('PlayerSeekBigForward')
@preflight_check
def alexa_player_seek_bigforward(kodi):
  card_title = render_template('big_step_forward').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSeekBigForward()
  return statement('').simple_card(card_title, '')


# Handle the PlayerSeekBigBackward intent.
@ask.intent('PlayerSeekBigBackward')
@preflight_check
def alexa_player_seek_bigbackward(kodi):
  card_title = render_template('big_step_backward').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSeekBigBackward()
  return statement('').simple_card(card_title, '')


def find_and_play(kodi, needle, content=['video','audio'], shuffle=False, slot_hint='unknown', slot_ignore=[]):
  log.info('Find and Play: "%s"', needle.encode('utf-8'))
  if slot_hint != 'unknown':
    log.info('Pre-match with slot: ' + slot_hint)
  log.info('Searching content types: ')
  log.info(content)

  # The order of the searches here is not random, please don't reorganize
  # without giving some thought to overall performance based on most
  # frequently requested types and user expectations.

  # Video playlist?
  if 'video' in content and 'VideoPlaylist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'VideoPlaylist'):
    playlist = kodi.FindVideoPlaylist(needle)
    if playlist:
      if shuffle:
        videos = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
        videos_array = []
        for video in videos:
          videos_array.append(video['file'])

        kodi.PlayerStop()
        kodi.ClearVideoPlaylist()
        kodi.AddVideosToPlaylist(videos_array, True)
        kodi.StartVideoPlaylist()
        op = render_template('shuffling_empty').encode('utf-8')
      else:
        kodi.PlayerStop()
        kodi.StartVideoPlaylist(playlist[0][0])
        op = render_template('playing_empty').encode('utf-8')
      return render_template('playing_playlist_video', action=op, playlist_name=playlist[0][1]).encode('utf-8')

  # Audio playlist?
  if 'audio' in content and 'AudioPlaylist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'AudioPlaylist'):
    playlist = kodi.FindAudioPlaylist(needle)
    if playlist:
      if shuffle:
        songs = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
        songs_array = []
        for song in songs:
          songs_array.append(song['id'])

        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongsToPlaylist(songs_array, True)
        kodi.StartAudioPlaylist()
        op = render_template('shuffling_empty').encode('utf-8')
      else:
        kodi.PlayerStop()
        kodi.StartAudioPlaylist(playlist[0][0])
        op = render_template('playing_empty').encode('utf-8')
      return render_template('playing_playlist_audio', action=op, playlist_name=playlist[0][1]).encode('utf-8')

  # Movie?
  if 'video' in content and 'Movie' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Movie'):
    movie = kodi.FindMovie(needle)
    if movie:
      if kodi.GetMovieDetails(movie[0][0])['resume']['position'] > 0:
        action = render_template('resuming_empty').encode('utf-8')
      else:
        action = render_template('playing_empty').encode('utf-8')
      kodi.PlayMovie(movie[0][0])
      return render_template('playing_action', action=action, movie_name=movie[0][1]).encode('utf-8')

  # Show?
  if 'video' in content and 'Show' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Show'):
    show = kodi.FindTvShow(needle)
    if show:
      episode_id = None
      episodes_array = []

      if shuffle:
        # Shuffle all episodes of the specified show
        episodes_result = kodi.GetEpisodesFromShow(show[0][0])
        for episode in episodes_result['result']['episodes']:
          episodes_array.append(episode['episodeid'])

        kodi.PlayerStop()
        kodi.ClearVideoPlaylist()
        kodi.AddEpisodesToPlaylist(episodes_array, shuffle)
        kodi.StartVideoPlaylist()
        return render_template('shuffling', heard_name=show[0][1]).encode('utf-8')
      else:
        # Try the next unwatched episode first
        episode_id = kodi.GetNextUnwatchedEpisode(show[0][0])
        if not episode_id:
          # All episodes already watched, so just play a random episode
          episodes_result = kodi.GetEpisodesFromShow(show[0][0])
          for episode in episodes_result['result']['episodes']:
            episodes_array.append(episode['episodeid'])
          episode_id = random.choice(episodes_array)

        if episode_id:
          episode_details = kodi.GetEpisodeDetails(episode_id)
          kodi.PlayEpisode(episode_id)
          return render_template('playing_episode_number', season=episode_details['season'], episode=episode_details['episode'], show_name=show[0][1]).encode('utf-8')

  # Music Video?
  if 'video' in content and 'MusicVideo' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'MusicVideo'):
    musicvideo = kodi.FindMusicVideo(needle)
    if musicvideo:
      musicvideo_details = kodi.GetMusicVideoDetails(musicvideo[0][0])
      kodi.PlayMusicVideo(musicvideo[0][0])
      return render_template('playing_musicvideo', musicvideo_name=musicvideo[0][1], artist_name=musicvideo_details['artist'][0]).encode('utf-8')

  # Artist?
  if 'audio' in content and 'Artist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Artist'):
    artist = kodi.FindArtist(needle)
    if artist:
      songs_result = kodi.GetArtistSongs(artist[0][0])
      songs = songs_result['result']['songs']
      songs_array = []
      for song in songs:
        songs_array.append(song['songid'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      # Always shuffle when generically requesting an Artist
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
      if shuffle:
        op = render_template('shuffling_empty').encode('utf-8')
      else:
        op = render_template('playing_empty').encode('utf-8')
      return render_template('playing_action', action=op, movie_name=artist[0][1]).encode('utf-8')

  # Song?
  if 'audio' in content and 'Song' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Song'):
    song = kodi.FindSong(needle)
    if song:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongToPlaylist(song[0][0])
      kodi.StartAudioPlaylist()
      return render_template('playing_song', song_name=song[0][1]).encode('utf-8')

  # Album?
  if 'audio' in content and 'Album' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Album'):
    album = kodi.FindAlbum(needle)
    if album:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(album[0][0], shuffle)
      kodi.StartAudioPlaylist()
      if shuffle:
        return render_template('shuffling_album', album_name=album[0][1]).encode('utf-8')
      else:
        return render_template('playing_album', album_name=album[0][1]).encode('utf-8')

  return ''


# Handle the ShuffleMedia intent.
#
# Generic shuffle function.  Tries to find media to play when the user didn't
# specify the media type.
#
# Matches directly to Show slot only, but will fuzzy match across the whole
# library if nothing found.
#
# See find_and_play() for the order of the searches.
@ask.intent('ShuffleMedia')
@preflight_check
def alexa_shuffle_media(kodi, Show=None):
  # Some media types don't make sense when shuffling
  ignore_slots = ['Movie', 'Song']

  card_title = render_template('shuffling', heard_name=Show).encode('utf-8')
  log.info(card_title)

  if not config.getboolean('global', 'deep_search'):
    response_text = render_template('help_play').encode('utf-8')
  else:
    response_text = find_and_play(kodi, Show, shuffle=True, slot_hint='Show', slot_ignore=ignore_slots)
    if not response_text:
      ignore_slots.append('Show')
      response_text = find_and_play(kodi, Show, shuffle=True, slot_ignore=ignore_slots)
    if not response_text:
      response_text = render_template('could_not_find', heard_name=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayMedia intent.
#
# Generic play function.  Tries to find media to play when the user didn't
# specify the media type.  Can be restricted to video or audio by passing
# in the array argument content, which is most useful when the user's verb
# is "listen to" or "watch".
#
# Matches directly to slots Movie and Artist only, but will fuzzy match
# across the whole library if neither are found.
#
# See find_and_play() for the order of the searches.
def _alexa_play_media(kodi, Movie=None, Artist=None, content=None, shuffle=False):
  if not content:
    content=['video','audio']

  heard_search = ''
  heard_slot = 'unknown'
  if 'video' in content and Movie:
    heard_search = Movie
    heard_slot = 'Movie'
  elif 'audio' in content and Artist:
    heard_search = Artist
    heard_slot = 'Artist'

  card_title = render_template('playing', heard_name=heard_search).encode('utf-8')
  log.info(card_title)

  if not config.getboolean('global', 'deep_search'):
    response_text = render_template('help_play').encode('utf-8')
  else:
    response_text = find_and_play(kodi, heard_search, content, shuffle, slot_hint=heard_slot)
    if not response_text and heard_slot != 'unknown':
      response_text = find_and_play(kodi, heard_search, content, shuffle, slot_ignore=[heard_slot])
    if not response_text:
      response_text = render_template('could_not_find', heard_name=heard_search).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


@ask.intent('PlayMedia')
@preflight_check
def alexa_play_media(kodi, Movie=None, Artist=None):
  return _alexa_play_media(kodi, Movie, Artist)


# Handle the ListenToAudio intent.
#
# Defaults to Artists, but will fuzzy match across the library if none found.
@ask.intent('ListenToAudio')
@preflight_check
def alexa_listen_audio(kodi, Artist):
  log.info('Listen to audio')
  return _alexa_play_media(kodi, Artist=Artist, content=['audio'])


# Handle the ListenToGenre intent (Shuffles all music of a specific genre).
@ask.intent('ListenToGenre')
@preflight_check
def alexa_listen_genre(kodi, MusicGenre):
  card_title = render_template('playing_genre', genre_name=MusicGenre).encode('utf-8')
  log.info(card_title)

  genre = kodi.FindMusicGenre(MusicGenre)
  if genre:
    songs_result = kodi.GetSongsByGenre(genre[0][1])
    if 'songs' in songs_result['result']:
      songs = songs_result['result']['songs']

      songs_array = []
      for song in songs:
        songs_array.append(song['songid'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
      response_text = render_template('playing_genre', genre_name=genre[0][1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_genre', genre_name=genre[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=MusicGenre).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToArtist intent (Shuffles all music by an artist, optionally of a specific genre).
@ask.intent('ListenToArtist')
@preflight_check
def alexa_listen_artist(kodi, Artist, MusicGenre):
  genre = []
  if MusicGenre:
    card_title = render_template('listen_artist_genre', heard_genre=MusicGenre, heard_artist=Artist).encode('utf-8')
    genre = kodi.FindMusicGenre(MusicGenre)
  else:
    card_title = render_template('listen_artist', heard_artist=Artist).encode('utf-8')
  log.info(card_title)

  artist = kodi.FindArtist(Artist)
  if artist:
    if genre:
      songs_result = kodi.GetArtistSongsByGenre(artist[0][1], genre[0][1])
      response_text = render_template('playing_genre_artist', genre_name=genre[0][1], artist_name=artist[0][1]).encode('utf-8')
    else:
      songs_result = kodi.GetArtistSongs(artist[0][0])
      response_text = render_template('playing', heard_name=artist[0][1]).encode('utf-8')
    if 'songs' in songs_result['result']:
      songs = songs_result['result']['songs']

      songs_array = []
      for song in songs:
        songs_array.append(song['songid'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
    elif genre:
      response_text = render_template('could_not_find_genre_artist', genre_name=genre[0][1], artist_name=artist[0][1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_artist', artist_name=artist[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def _alexa_listen_album(kodi, Album, Artist, shuffle=False):
  if shuffle:
    card_title = render_template('shuffling_album_card').encode('utf-8')
  else:
    card_title = render_template('playing_album_card').encode('utf-8')
  log.info(card_title)

  album = None
  response_text = ''
  if Artist:
    artist = kodi.FindArtist(Artist)
    if artist:
      for a in artist:
        log.info('Searching albums by "%s"', a[1].encode('utf-8'))
        album = kodi.FindAlbum(Album, a[0])
        if album:
          if shuffle:
            response_text = render_template('shuffling_album_artist', album_name=album[0][1], artist=a[1]).encode('utf-8')
          else:
            response_text = render_template('playing_album_artist', album_name=album[0][1], artist=a[1]).encode('utf-8')
          break
        elif not response_text:
          response_text = render_template('could_not_find_album_artist', album_name=Album, artist=a[1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_album_artist', album_name=Album, artist=Artist).encode('utf-8')
  else:
    album = kodi.FindAlbum(Album)
    if album:
      if shuffle:
        response_text = render_template('shuffling_album', album_name=album[0][1]).encode('utf-8')
      else:
        response_text = render_template('playing_album', album_name=album[0][1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_album', album_name=Album).encode('utf-8')

  if album:
    kodi.PlayerStop()
    kodi.ClearAudioPlaylist()
    kodi.AddAlbumToPlaylist(album[0][0], shuffle)
    kodi.StartAudioPlaylist()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAlbum intent (Play whole album, or whole album by a specific artist).
@ask.intent('ListenToAlbum')
@preflight_check
def alexa_listen_album(kodi, Album, Artist):
  return _alexa_listen_album(kodi, Album, Artist)


# Handle the ShuffleAlbum intent (Shuffle whole album, or whole album by a specific artist).
@ask.intent('ShuffleAlbum')
@preflight_check
def alexa_shuffle_album(kodi, Album, Artist):
  return _alexa_listen_album(kodi, Album, Artist, True)


def _alexa_listen_latest_album(kodi, Artist, shuffle=False):
  if shuffle:
    card_title = render_template('shuffling_latest_album_card', heard_artist=Artist).encode('utf-8')
  else:
    card_title = render_template('playing_latest_album_card', heard_artist=Artist).encode('utf-8')
  log.info(card_title)

  artist = kodi.FindArtist(Artist)
  if artist:
    album_id = kodi.GetNewestAlbumFromArtist(artist[0][0])
    if album_id:
      album_label = kodi.GetAlbumDetails(album_id)['label']
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(album_id, shuffle)
      kodi.StartAudioPlaylist()
      if shuffle:
        response_text = render_template('shuffling_album_artist', album_name=album_label, artist=artist[0][1]).encode('utf-8')
      else:
        response_text = render_template('playing_album_artist', album_name=album_label, artist=artist[0][1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_artist', artist_name=artist[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToLatestAlbum intent (Play latest album by a specific artist).
@ask.intent('ListenToLatestAlbum')
@preflight_check
def alexa_listen_latest_album(kodi, Artist):
  return _alexa_listen_latest_album(kodi, Artist)


# Handle the ShuffleLatestAlbum intent (Shuffle latest album by a specific artist).
@ask.intent('ShuffleLatestAlbum')
@preflight_check
def alexa_shuffle_latest_album(kodi, Artist):
  return _alexa_listen_latest_album(kodi, Artist, True)


# Handle the ListenToSong intent (Play a song, song by a specific artist,
# or song on a specific album).
@ask.intent('ListenToSong')
@preflight_check
def alexa_listen_song(kodi, Song, Album, Artist):
  card_title = render_template('playing_song_card').encode('utf-8')
  log.info(card_title)

  response_text = ''
  song = None
  if Artist:
    artist = kodi.FindArtist(Artist)
    if artist:
      for a in artist:
        log.info('Searching songs by "%s"', a[1].encode('utf-8'))
        song = kodi.FindSong(Song, a[0])
        if song:
          response_text = render_template('playing_song_artist', song_name=song[0][1], artist=a[1]).encode('utf-8')
          break
        elif not response_text:
          response_text = render_template('could_not_find_song_artist', song_name=Song, artist=a[1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_song_artist', song_name=Song, artist=Artist).encode('utf-8')
  elif Album:
    album = kodi.FindAlbum(Album)
    if album:
      for a in album:
        log.info('Searching on album "%s"', a[1].encode('utf-8'))
        song = kodi.FindSong(Song, album_id=a[0])
        if song:
          response_text = render_template('playing_song_album', song_name=song[0][1], album_name=a[1]).encode('utf-8')
          break
        elif not response_text:
          response_text = render_template('could_not_find_song_album', song_name=Song, album_name=a[1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_song_album', song_name=Song, album_name=Album).encode('utf-8')
  else:
    song = kodi.FindSong(Song)
    if song:
      response_text = render_template('playing_song', song_name=song[0][1]).encode('utf-8')
    else:
      response_text = render_template('could_not_find_song', song_name=Song).encode('utf-8')

  if song:
    kodi.PlayerStop()
    kodi.ClearAudioPlaylist()
    kodi.AddSongToPlaylist(song[0][0])
    kodi.StartAudioPlaylist()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAlbumOrSong intent (Play whole album or song by a specific artist).
@ask.intent('ListenToAlbumOrSong')
@preflight_check
def alexa_listen_album_or_song(kodi, Song, Artist):
  card_title = render_template('playing_album_or_song').encode('utf-8')
  log.info(card_title)

  response_text = ''

  artist = kodi.FindArtist(Artist)
  if artist:
    for a in artist:
      log.info('Searching songs and albums by "%s"', a[1].encode('utf-8'))
      song = kodi.FindSong(Song, a[0])
      if song:
        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongToPlaylist(song[0][0])
        kodi.StartAudioPlaylist()
        response_text = render_template('playing_song_artist', song_name=song[0][1], artist=a[1]).encode('utf-8')
        break
      else:
        album = kodi.FindAlbum(Song, a[0])
        if album:
          kodi.PlayerStop()
          kodi.ClearAudioPlaylist()
          kodi.AddAlbumToPlaylist(album[0][0])
          kodi.StartAudioPlaylist()
          response_text = render_template('playing_album_artist', album_name=album[0][1], artist=a[1]).encode('utf-8')
          break
        elif not response_text:
          response_text = render_template('could_not_find_multi', heard_name=Song, artist=a[1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAudioPlaylistRecent intent (Shuffle all recently added songs).
@ask.intent('ListenToAudioPlaylistRecent')
@preflight_check
def alexa_listen_recently_added_songs(kodi):
  card_title = render_template('playing_recent_songs').encode('utf-8')
  log.info(card_title)

  response_text = render_template('no_recent_songs').encode('utf-8')

  songs_result = kodi.GetRecentlyAddedSongs()
  if songs_result:
    songs = songs_result['result']['songs']

    songs_array = []
    for song in songs:
      songs_array.append(song['songid'])

    kodi.PlayerStop()
    kodi.ClearAudioPlaylist()
    kodi.AddSongsToPlaylist(songs_array, True)
    kodi.StartAudioPlaylist()
    response_text = render_template('playing_recent_songs').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def _alexa_listen_audio_playlist(kodi, AudioPlaylist, shuffle=False):
  if shuffle:
    op = render_template('shuffling_empty').encode('utf-8')
  else:
    op = render_template('playing_empty').encode('utf-8')

  card_title = render_template('action_audio_playlist', action=op).encode('utf-8')
  log.info(card_title)

  playlist = kodi.FindAudioPlaylist(AudioPlaylist)
  if playlist:
    if shuffle:
      songs = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
      songs_array = []
      for song in songs:
        songs_array.append(song['id'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
    else:
      kodi.PlayerStop()
      kodi.StartAudioPlaylist(playlist[0][0])
    response_text = render_template('playing_playlist_audio', action=op, playlist_name=playlist[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_playlist', heard_name=AudioPlaylist).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAudioPlaylist intent.
@ask.intent('ListenToAudioPlaylist')
@preflight_check
def alexa_listen_audio_playlist(kodi, AudioPlaylist):
  return _alexa_listen_audio_playlist(kodi, AudioPlaylist)


# Handle the ShuffleAudioPlaylist intent.
@ask.intent('ShuffleAudioPlaylist')
@preflight_check
def alexa_shuffle_audio_playlist(kodi, AudioPlaylist):
  return _alexa_listen_audio_playlist(kodi, AudioPlaylist, True)


# Handle the PartyMode intent.
@ask.intent('PartyMode')
@preflight_check
def alexa_party_play(kodi):
  card_title = render_template('party_mode').encode('utf-8')
  log.info(card_title)

  kodi.PlayerStop()
  kodi.ClearAudioPlaylist()
  kodi.PartyPlayMusic()
  response_text = render_template('playing_party').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.StartOverIntent intent.
@ask.intent('AMAZON.StartOverIntent')
@preflight_check
def alexa_start_over(kodi):
  card_title = render_template('playing_same').encode('utf-8')
  log.info(card_title)

  kodi.PlayerStartOver()
  return statement('').simple_card(card_title, '')


# Handle the AMAZON.NextIntent intent.
@ask.intent('AMAZON.NextIntent')
@preflight_check
def alexa_next(kodi):
  card_title = render_template('playing_next').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSkip()
  return statement('').simple_card(card_title, '')


# Handle the AMAZON.PreviousIntent intent.
@ask.intent('AMAZON.PreviousIntent')
@preflight_check
def alexa_prev(kodi):
  card_title = render_template('playing_previous').encode('utf-8')
  log.info(card_title)

  kodi.PlayerPrev()
  return statement('').simple_card(card_title, '')


# Handle the AMAZON.ShuffleOnIntent intent.
@ask.intent('AMAZON.ShuffleOnIntent')
@preflight_check
def alexa_shuffle_on(kodi):
  card_title = render_template('shuffle_enable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerShuffleOn()
  response_text = render_template('shuffle_on').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.ShuffleOffIntent intent.
@ask.intent('AMAZON.ShuffleOffIntent')
@preflight_check
def alexa_shuffle_off(kodi):
  card_title = render_template('shuffle_disable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerShuffleOff()
  response_text = render_template('shuffle_off').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.LoopOnIntent intent.
@ask.intent('AMAZON.LoopOnIntent')
@preflight_check
def alexa_loop_on(kodi):
  card_title = render_template('loop_enable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerLoopOn()

  response_text = ''

  curprops = kodi.GetActivePlayProperties()
  if curprops is not None:
    if curprops['repeat'] == 'one':
      response_text = render_template('loop_one').encode('utf-8')
    elif curprops['repeat'] == 'all':
      response_text = render_template('loop_all').encode('utf-8')
    elif curprops['repeat'] == 'off':
      response_text = render_template('loop_off').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.LoopOffIntent intent.
@ask.intent('AMAZON.LoopOffIntent')
@preflight_check
def alexa_loop_off(kodi):
  card_title = render_template('loop_disable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerLoopOff()
  response_text = render_template('loop_off').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the Fullscreen intent.
@ask.intent('Fullscreen')
@preflight_check
def alexa_fullscreen(kodi):
  card_title = render_template('toggle_fullscreen').encode('utf-8')
  log.info(card_title)

  kodi.ToggleFullscreen()
  return statement('').simple_card(card_title, '')


# Handle the StereoscopicMode intent.
@ask.intent('StereoscopicMode')
@preflight_check
def alexa_stereoscopic_mode(kodi):
  card_title = render_template('toggle_stereoscopic_mode').encode('utf-8')
  log.info(card_title)

  kodi.ToggleStereoscopicMode()
  return statement('').simple_card(card_title, '')


# Handle the AudioPassthrough intent.
@ask.intent('AudioPassthrough')
@preflight_check
def alexa_audio_passthrough(kodi):
  card_title = render_template('toggle_audio_passthrough').encode('utf-8')
  log.info(card_title)

  kodi.ToggleAudioPassthrough()
  return statement('').simple_card(card_title, '')


# Handle the Mute intent.
@ask.intent('Mute')
@preflight_check
def alexa_mute(kodi):
  card_title = render_template('mute_unmute').encode('utf-8')
  log.info(card_title)

  kodi.ToggleMute()
  return statement('').simple_card(card_title, '')


# Handle the VolumeUp intent.
@ask.intent('VolumeUp')
@preflight_check
def alexa_volume_up(kodi):
  card_title = render_template('volume_up').encode('utf-8')
  log.info(card_title)

  vol = kodi.VolumeUp()['result']
  response_text = render_template('volume_set', num=vol).encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeDown intent.
@ask.intent('VolumeDown')
@preflight_check
def alexa_volume_down(kodi):
  card_title = render_template('volume_down').encode('utf-8')
  log.info(card_title)

  vol = kodi.VolumeDown()['result']
  response_text = render_template('volume_set', num=vol).encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeSet intent.
@ask.intent('VolumeSet')
@preflight_check
def alexa_volume_set(kodi, Volume):
  card_title = render_template('adjusting_volume').encode('utf-8')
  log.info(card_title)

  vol = kodi.VolumeSet(int(Volume), False)['result']
  response_text = render_template('volume_set', num=vol).encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeSetPct intent.
@ask.intent('VolumeSetPct')
@preflight_check
def alexa_volume_set_pct(kodi, Volume):
  card_title = render_template('adjusting_volume').encode('utf-8')
  log.info(card_title)

  vol = kodi.VolumeSet(int(Volume))['result']
  response_text = render_template('volume_set', num=vol).encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesOn intent.
@ask.intent('SubtitlesOn')
@preflight_check
def alexa_subtitles_on(kodi):
  card_title = render_template('subtitles_enable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSubtitlesOn()
  response_text = kodi.GetCurrentSubtitles()
  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesOff intent.
@ask.intent('SubtitlesOff')
@preflight_check
def alexa_subtitles_off(kodi):
  card_title = render_template('subtitles_disable').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSubtitlesOff()
  response_text = render_template('subtitles_disable').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesNext intent.
@ask.intent('SubtitlesNext')
@preflight_check
def alexa_subtitles_next(kodi):
  card_title = render_template('subtitles_next').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSubtitlesNext()
  response_text = kodi.GetCurrentSubtitles()
  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesPrevious intent.
@ask.intent('SubtitlesPrevious')
@preflight_check
def alexa_subtitles_previous(kodi):
  card_title = render_template('subtitles_previous').encode('utf-8')
  log.info(card_title)

  kodi.PlayerSubtitlesPrevious()
  response_text = kodi.GetCurrentSubtitles()
  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesDownload intent.
@ask.intent('SubtitlesDownload')
@preflight_check
def alexa_subtitles_download(kodi):
  card_title = render_template('subtitles_download').encode('utf-8')
  log.info(card_title)

  item = kodi.DownloadSubtitles()
  return statement(card_title).simple_card(card_title, '')


# Handle the AudioStreamNext intent.
@ask.intent('AudioStreamNext')
@preflight_check
def alexa_audiostream_next(kodi):
  card_title = render_template('audio_stream_next').encode('utf-8')
  log.info(card_title)

  kodi.PlayerAudioStreamNext()
  response_text = kodi.GetCurrentAudioStream()
  return statement(response_text).simple_card(card_title, response_text)


# Handle the AudioStreamPrevious intent.
@ask.intent('AudioStreamPrevious')
@preflight_check
def alexa_audiostream_previous(kodi):
  card_title = render_template('audio_stream_previous').encode('utf-8')
  log.info(card_title)

  kodi.PlayerAudioStreamPrevious()
  response_text = kodi.GetCurrentAudioStream()
  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerMoveUp intent.
@ask.intent('PlayerMoveUp')
@preflight_check
def alexa_player_move_up(kodi):
  card_title = render_template('player_move_up').encode('utf-8')
  log.info(card_title)

  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerMoveDown intent.
@ask.intent('PlayerMoveDown')
@preflight_check
def alexa_player_move_down(kodi):
  card_title = render_template('player_move_down').encode('utf-8')
  log.info(card_title)

  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerMoveLeft intent.
@ask.intent('PlayerMoveLeft')
@preflight_check
def alexa_player_move_left(kodi):
  card_title = render_template('player_move_left').encode('utf-8')
  log.info(card_title)

  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerMoveRight intent.
@ask.intent('PlayerMoveRight')
@preflight_check
def alexa_player_move_right(kodi):
  card_title = render_template('player_move_right').encode('utf-8')
  log.info(card_title)

  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerRotateClockwise intent.
@ask.intent('PlayerRotateClockwise')
@preflight_check
def alexa_player_rotate_clockwise(kodi):
  card_title = render_template('player_rotate').encode('utf-8')
  log.info(card_title)

  kodi.PlayerRotateClockwise()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerRotateCounterClockwise intent.
@ask.intent('PlayerRotateCounterClockwise')
@preflight_check
def alexa_player_rotate_counterclockwise(kodi):
  card_title = render_template('player_rotate_cc').encode('utf-8')
  log.info(card_title)

  kodi.PlayerRotateCounterClockwise()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomHold intent.
@ask.intent('PlayerZoomHold')
@preflight_check
def alexa_player_zoom_hold(kodi):
  card_title = render_template('player_zoom_hold').encode('utf-8')
  log.info(card_title)

  response_text = ''
  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerZoomIn intent.
@ask.intent('PlayerZoomIn')
@preflight_check
def alexa_player_zoom_in(kodi):
  card_title = render_template('player_zoom_in').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomIn()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomInMoveUp intent.
@ask.intent('PlayerZoomInMoveUp')
@preflight_check
def alexa_player_zoom_in_move_up(kodi):
  card_title = render_template('player_zoom_in_up').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomIn()
  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomInMoveDown intent.
@ask.intent('PlayerZoomInMoveDown')
@preflight_check
def alexa_player_zoom_in_move_down(kodi):
  card_title = render_template('player_zoom_in_down').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomIn()
  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomInMoveLeft intent.
@ask.intent('PlayerZoomInMoveLeft')
@preflight_check
def alexa_player_zoom_in_move_left(kodi):
  card_title = render_template('player_zoom_in_left').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomIn()
  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomInMoveRight intent.
@ask.intent('PlayerZoomInMoveRight')
@preflight_check
def alexa_player_zoom_in_move_right(kodi):
  card_title = render_template('player_zoom_in_right').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomIn()
  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomOut intent.
@ask.intent('PlayerZoomOut')
@preflight_check
def alexa_player_zoom_out(kodi):
  card_title = render_template('player_zoom_out').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomOut()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomOutMoveUp intent.
@ask.intent('PlayerZoomOutMoveUp')
@preflight_check
def alexa_player_zoom_out_move_up(kodi):
  card_title = render_template('player_zoom_out_up').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomOut()
  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomOutMoveDown intent.
@ask.intent('PlayerZoomOutMoveDown')
@preflight_check
def alexa_player_zoom_out_move_down(kodi):
  card_title = render_template('player_zoom_out_down').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomOut()
  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomOutMoveLeft intent.
@ask.intent('PlayerZoomOutMoveLeft')
@preflight_check
def alexa_player_zoom_out_move_left(kodi):
  card_title = render_template('player_zoom_out_left').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomOut()
  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomOutMoveRight intent.
@ask.intent('PlayerZoomOutMoveRight')
@preflight_check
def alexa_player_zoom_out_move_right(kodi):
  card_title = render_template('player_zoom_out_right').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoomOut()
  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PlayerZoomReset intent.
@ask.intent('PlayerZoomReset')
@preflight_check
def alexa_player_zoom_reset(kodi):
  card_title = render_template('player_zoom_normal').encode('utf-8')
  log.info(card_title)

  kodi.PlayerZoom(1)
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Menu intent.
@ask.intent('Menu')
@preflight_check
def alexa_context_menu(kodi):
  log.info('Navigate: Context Menu')

  kodi.Menu()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Home intent.
@ask.intent('Home')
@preflight_check
def alexa_go_home(kodi):
  log.info('Navigate: Home')

  kodi.Home()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Select intent.
@ask.intent('Select')
@preflight_check
def alexa_select(kodi):
  log.info('Navigate: Select')

  kodi.Select()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PageUp intent.
@ask.intent('PageUp')
@preflight_check
def alexa_pageup(kodi):
  log.info('Navigate: Page up')

  kodi.PageUp()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the PageDown intent.
@ask.intent('PageDown')
@preflight_check
def alexa_pagedown(kodi):
  log.info('Navigate: Page down')

  kodi.PageDown()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Left intent.
@ask.intent('Left')
@preflight_check
def alexa_left(kodi):
  log.info('Navigate: Left')

  kodi.Left()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Right intent.
@ask.intent('Right')
@preflight_check
def alexa_right(kodi):
  log.info('Navigate: Right')

  kodi.Right()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Up intent.
@ask.intent('Up')
@preflight_check
def alexa_up(kodi):
  log.info('Navigate: Up')

  kodi.Up()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Down intent.
@ask.intent('Down')
@preflight_check
def alexa_down(kodi):
  log.info('Navigate: Down')

  kodi.Down()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Back intent.
@ask.intent('Back')
@preflight_check
def alexa_back(kodi):
  log.info('Navigate: Back')

  kodi.Back()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Info intent.
@ask.intent('Info')
@preflight_check
def alexa_info(kodi):
  log.info('Navigate: Info')

  kodi.Info()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewMovies intent.
@ask.intent('ViewMovies')
@preflight_check
def alexa_show_movies(kodi, MovieGenre):
  log.info('Navigate: Movies')

  genre = None
  if MovieGenre:
    g = kodi.FindVideoGenre(MovieGenre)
    if g:
      genre = g[0][0]
  kodi.ShowMovies(genre)
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewShows intent.
@ask.intent('ViewShows')
@preflight_check
def alexa_show_shows(kodi, ShowGenre):
  log.info('Navigate: Shows')

  genre = None
  if ShowGenre:
    g = kodi.FindVideoGenre(ShowGenre, 'tvshow')
    if g:
      genre = g[0][0]
  kodi.ShowTvShows(genre)
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewMusicVideos intent.
@ask.intent('ViewMusicVideos')
@preflight_check
def alexa_show_music_videos(kodi, MusicVideoGenre):
  log.info('Navigate: MusicVideos')

  genre = None
  if MusicVideoGenre:
    g = kodi.FindVideoGenre(MusicVideoGenre, 'musicvideo')
    if g:
      genre = g[0][0]
  kodi.ShowMusicVideos(genre)
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewMusic intent.
@ask.intent('ViewMusic')
@preflight_check
def alexa_show_music(kodi, MusicGenre):
  log.info('Navigate: Music')

  genre = None
  if MusicGenre:
    g = kodi.FindMusicGenre(MusicGenre)
    if g:
      genre = g[0][0]
  kodi.ShowMusic(genre)
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewArtists intent.
@ask.intent('ViewArtists')
@preflight_check
def alexa_show_artists(kodi):
  log.info('Navigate: Artists')

  kodi.ShowMusicArtists()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewAlbums intent.
@ask.intent('ViewAlbums')
@preflight_check
def alexa_show_albums(kodi):
  log.info('Navigate: Albums')

  kodi.ShowMusicAlbums()
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewVideoPlaylist intent.
@ask.intent('ViewVideoPlaylist')
@preflight_check
def alexa_show_video_playlist(kodi, VideoPlaylist):
  log.info('Navigate: Video Playlist')

  playlist = kodi.FindVideoPlaylist(VideoPlaylist)
  if playlist:
    kodi.ShowVideoPlaylist(playlist[0][0])
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewMoviePlaylistRecent intent.
@ask.intent('ViewMoviePlaylistRecent')
@preflight_check
def alexa_show_recent_movies_playlist(kodi):
  log.info('Navigate: Recently Added Movies')

  kodi.ShowVideoPlaylist('videodb://recentlyaddedmovies/')
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewEpisodePlaylistRecent intent.
@ask.intent('ViewEpisodePlaylistRecent')
@preflight_check
def alexa_show_recent_episodes_playlist(kodi):
  log.info('Navigate: Recently Added Episodes')

  kodi.ShowVideoPlaylist('videodb://recentlyaddedepisodes/')
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewMusicVideoPlaylistRecent intent.
@ask.intent('ViewMusicVideoPlaylistRecent')
@preflight_check
def alexa_show_recent_musicvideos_playlist(kodi):
  log.info('Navigate: Recently Added Music Videos')

  kodi.ShowVideoPlaylist('videodb://recentlyaddedmusicvideos/')
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewAudioPlaylist intent.
@ask.intent('ViewAudioPlaylist')
@preflight_check
def alexa_show_audio_playlist(kodi, AudioPlaylist):
  log.info('Navigate: Audio Playlist')

  playlist = kodi.FindAudioPlaylist(AudioPlaylist)
  if playlist:
    kodi.ShowMusicPlaylist(playlist[0][0])
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewAudioPlaylistRecent intent.
@ask.intent('ViewAudioPlaylistRecent')
@preflight_check
def alexa_show_recent_audio_playlist(kodi):
  log.info('Navigate: Recently Added Albums')

  kodi.ShowMusicPlaylist('musicdb://recentlyaddedalbums/')
  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the ViewPlaylist intent.
@ask.intent('ViewPlaylist')
@preflight_check
def alexa_show_playlist(kodi, VideoPlaylist, AudioPlaylist):
  log.info('Navigate: Playlist')

  heard_search = ''
  if VideoPlaylist:
    heard_search = VideoPlaylist
  elif AudioPlaylist:
    heard_search = AudioPlaylist

  if heard_search:
    playlist = kodi.FindVideoPlaylist(heard_search)
    if playlist:
      kodi.ShowVideoPlaylist(playlist[0][0])
    else:
      playlist = kodi.FindAudioPlaylist(heard_search)
      if playlist:
        kodi.ShowMusicPlaylist(playlist[0][0])

  response_text = render_template('short_confirm').encode('utf-8')
  return question(response_text)


# Handle the Shutdown intent.
@ask.intent('Shutdown')
@preflight_check
def alexa_shutdown(kodi):
  response_text = render_template('are_you_sure_shutdown').encode('utf-8')
  session.attributes['shutting_down'] = True
  return question(response_text).reprompt(response_text)


# Handle the Reboot intent.
@ask.intent('Reboot')
@preflight_check
def alexa_reboot(kodi):
  response_text = render_template('are_you_sure_reboot').encode('utf-8')
  session.attributes['rebooting'] = True
  return question(response_text).reprompt(response_text)


# Handle the Hibernate intent.
@ask.intent('Hibernate')
@preflight_check
def alexa_hibernate(kodi):
  response_text = render_template('are_you_sure_hibernate').encode('utf-8')
  session.attributes['hibernating'] = True
  return question(response_text).reprompt(response_text)


# Handle the Suspend intent.
@ask.intent('Suspend')
@preflight_check
def alexa_suspend(kodi):
  response_text = render_template('are_you_sure_suspend').encode('utf-8')
  session.attributes['suspending'] = True
  return question(response_text).reprompt(response_text)


# Handle the EjectMedia intent.
@ask.intent('EjectMedia')
@preflight_check
def alexa_ejectmedia(kodi):
  card_title = render_template('ejecting_media').encode('utf-8')
  log.info(card_title)

  kodi.SystemEjectMedia()

  if not 'queries_keep_open' in session.attributes:
    return statement(card_title).simple_card(card_title, '')

  return question(card_title)


# Handle the CleanVideo intent.
@ask.intent('CleanVideo')
@preflight_check
def alexa_clean_video(kodi):
  card_title = render_template('clean_video').encode('utf-8')
  log.info(card_title)

  kodi.CleanVideo()
  return statement(card_title).simple_card(card_title, '')


# Handle the UpdateVideo intent.
@ask.intent('UpdateVideo')
@preflight_check
def alexa_update_video(kodi):
  card_title = render_template('update_video').encode('utf-8')
  log.info(card_title)

  kodi.UpdateVideo()
  return statement(card_title).simple_card(card_title, '')


# Handle the CleanAudio intent.
@ask.intent('CleanAudio')
@preflight_check
def alexa_clean_audio(kodi):
  card_title = render_template('clean_audio').encode('utf-8')
  log.info(card_title)

  kodi.CleanMusic()
  return statement(card_title).simple_card(card_title, '')


# Handle the UpdateAudio intent.
@ask.intent('UpdateAudio')
@preflight_check
def alexa_update_audio(kodi):
  card_title = render_template('update_audio').encode('utf-8')
  log.info(card_title)

  kodi.UpdateMusic()
  return statement(card_title).simple_card(card_title, '')


# Handle the AddonExecute intent.
@ask.intent('AddonExecute')
@preflight_check
def alexa_addon_execute(kodi, Addon):
  card_title = render_template('open_addon').encode('utf-8')
  log.info(card_title)

  addon = kodi.FindAddon(Addon)
  if addon:
    kodi.Home()
    kodi.AddonExecute(addon[0][0])
    response_text = render_template('opening', heard_name=addon[0][1]).encode('utf-8')
    return statement(response_text).simple_card(card_title, response_text)
  else:
    response_text = render_template('could_not_find_addon', heard_addon=Addon).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)

# Handle the AddonGlobalSearch intent.
@ask.intent('AddonGlobalSearch')
@preflight_check
def alexa_addon_globalsearch(kodi, Movie, Show, Artist, Album, Song):
  card_title = render_template('search').encode('utf-8')
  log.info(card_title)
  heard_search = ''

  if Movie:
    heard_search = Movie
  elif Show:
    heard_search = Show
  elif Artist:
    heard_search = Artist
  elif Album:
    heard_search = Album
  elif Song:
    heard_search = Song

  if heard_search:
    kodi.Home()
    kodi.AddonGlobalSearch(heard_search)
    response_text = render_template('searching', heard_name=heard_search).encode('utf-8')
  else:
    response_text = render_template('could_not_find_generic').encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text).reprompt(response_text)


# Handle the WatchVideo intent.
#
# Defaults to Movies, but will fuzzy match across the library if none found.
@ask.intent('WatchVideo')
@preflight_check
def alexa_watch_video(kodi, Movie):
  log.info('Watch a video...')
  return _alexa_play_media(kodi, Movie=Movie, content=['video'])


# Handle the WatchRandomMovie intent.
@ask.intent('WatchRandomMovie')
@preflight_check
def alexa_watch_random_movie(kodi, MovieGenre):
  genre = []
  # If a genre has been specified, match the genre for use in selecting a random film
  if MovieGenre:
    card_title = render_template('playing_random_movie_genre', genre=MovieGenre).encode('utf-8')
    genre = kodi.FindVideoGenre(MovieGenre)
  else:
    card_title = render_template('playing_random_movie').encode('utf-8')
  log.info(card_title)

  # Select from specified genre if one was matched
  movies_array = []
  if genre:
    movies_array = kodi.GetUnwatchedMoviesByGenre(genre[0][1])
  else:
    movies_array = kodi.GetUnwatchedMovies()
  if not movies_array:
    # Fall back to all movies if no unwatched available
    if genre:
      movies = kodi.GetMoviesByGenre(genre[0][1])
    else:
      movies = kodi.GetMovies()
    if 'result' in movies and 'movies' in movies['result']:
      movies_array = movies['result']['movies']

  if movies_array:
    random_movie = random.choice(movies_array)
    kodi.PlayMovie(random_movie['movieid'], False)
    if genre:
      response_text = render_template('playing_genre_movie', genre=genre[0][1], movie_name=random_movie['label']).encode('utf-8')
    else:
      response_text = render_template('playing', heard_name=random_movie['label']).encode('utf-8')
  else:
    response_text = render_template('error_parsing_results').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchMovie intent.
@ask.intent('WatchMovie')
@preflight_check
def alexa_watch_movie(kodi, Movie):
  card_title = render_template('playing_movie').encode('utf-8')
  log.info(card_title)

  movie = kodi.FindMovie(Movie)
  if movie:
    kodi.PlayMovie(movie[0][0])
    if kodi.GetMovieDetails(movie[0][0])['resume']['position'] > 0:
      action = render_template('resuming_empty').encode('utf-8')
    else:
      action = render_template('playing_empty').encode('utf-8')
    response_text = render_template('playing_action', action=action, movie_name=movie[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_movie', heard_movie=Movie).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchMovieTrailer intent.
@ask.intent('WatchMovieTrailer')
@preflight_check
def alexa_watch_movie_trailer(kodi, Movie):
  card_title = render_template('playing_movie_trailer').encode('utf-8')
  log.info(card_title)

  movie_id = None
  # If we're currently recommending a movie to the user, let's assume that
  # they're wanting to watch the trailer for that.
  if 'play_media_type' in session.attributes and session.attributes['play_media_type'] == 'movie':
    movie_id = session.attributes['play_media_id']
  elif Movie:
    movie = kodi.FindMovie(Movie)
    if movie:
      movie_id = movie[0][0]

  if movie_id:
    movie_details = kodi.GetMovieDetails(movie_id)
    if 'trailer' in movie_details and movie_details['trailer']:
      kodi.PlayFile(movie_details['trailer'])
      response_text = render_template('playing_trailer', heard_name=movie_details['label']).encode('utf-8')
    else:
      response_text = render_template('could_not_find_trailer', heard_name=Movie).encode('utf-8')
  elif Movie:
    response_text = render_template('could_not_find_movie', heard_movie=Movie).encode('utf-8')
  else:
    response_text = render_template('could_not_find_generic').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleShow intent.
@ask.intent('ShuffleShow')
@preflight_check
def alexa_shuffle_show(kodi, Show):
  card_title = render_template('shuffling_episodes', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    episodes_array = []
    episodes_result = kodi.GetEpisodesFromShow(show[0][0])
    for episode in episodes_result['result']['episodes']:
      episodes_array.append(episode['episodeid'])

    kodi.PlayerStop()
    kodi.ClearVideoPlaylist()
    kodi.AddEpisodesToPlaylist(episodes_array, True)
    kodi.StartVideoPlaylist()
    response_text = render_template('shuffling', heard_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def _alexa_watch_random_episode(kodi, Show):
  card_title = render_template('playing_random_episode', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    episodes_result = kodi.GetEpisodesFromShow(show[0][0])

    episodes_array = []
    for episode in episodes_result['result']['episodes']:
      episodes_array.append(episode['episodeid'])

    episode_id = random.choice(episodes_array)
    episode_details = kodi.GetEpisodeDetails(episode_id)

    kodi.PlayEpisode(episode_id, False)
    response_text = render_template('playing_episode_number', season=episode_details['season'], episode=episode_details['episode'], show_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchRandomEpisode intent.
@ask.intent('WatchRandomEpisode')
@preflight_check
def alexa_watch_random_episode(kodi, Show):
  return _alexa_watch_random_episode(kodi, Show)


# Handle the WatchRandomShow intent.
@ask.intent('WatchRandomShow')
@preflight_check
def alexa_watch_random_show(kodi, ShowGenre):
  genre = []
  # If a genre has been specified, match the genre for use in selecting a random show
  if ShowGenre:
    card_title = render_template('playing_random_show_genre', genre=ShowGenre).encode('utf-8')
    genre = kodi.FindVideoGenre(ShowGenre, 'tvshow')
  else:
    card_title = render_template('playing_random_show').encode('utf-8')
  log.info(card_title)

  # Select from specified genre if one was matched
  if genre:
    shows_array = kodi.GetUnwatchedShowsByGenre(genre[0][1])
  else:
    shows_array = kodi.GetUnwatchedShows()
  if shows_array:
    random_show = random.choice(shows_array)
    return _alexa_watch_next_episode(kodi, random_show['label'])
  else:
    # Fall back to all shows if no unwatched available
    if genre:
      shows = kodi.GetShowsByGenre(genre[0][1])
    else:
      shows = kodi.GetShows()
    if 'result' in shows and 'tvshows' in shows['result']:
      shows_array = shows['result']['tvshows']
      random_show = random.choice(shows_array)
      return _alexa_watch_random_episode(kodi, random_show['label'])

  response_text = render_template('error_parsing_results').encode('utf-8')
  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchEpisode intent.
@ask.intent('WatchEpisode')
@preflight_check
def alexa_watch_episode(kodi, Show, Season, Episode):
  card_title = render_template('playing_an_episode', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    episode_id = kodi.GetSpecificEpisode(show[0][0], Season, Episode)
    if episode_id:
      kodi.PlayEpisode(episode_id)

      if kodi.GetEpisodeDetails(episode_id)['resume']['position'] > 0:
        action = render_template('resuming_empty').encode('utf-8')
      else:
        action = render_template('playing_empty').encode('utf-8')
      response_text = render_template('playing_action_episode_number', action=action, season=Season, episode=Episode, show_name=show[0][1]).encode('utf-8')

    else:
      response_text = render_template('could_not_find_episode_show', season=Season, episode=Episode, show_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def _alexa_watch_next_episode(kodi, Show):
  card_title = render_template('playing_next_unwatched_episode', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    next_episode_id = kodi.GetNextUnwatchedEpisode(show[0][0])
    if next_episode_id:
      kodi.PlayEpisode(next_episode_id)

      episode_details = kodi.GetEpisodeDetails(next_episode_id)
      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode('utf-8')
      else:
        action = render_template('playing_empty').encode('utf-8')
      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=show[0][1]).encode('utf-8')
    else:
      response_text = render_template('no_new_episodes_show', show_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchNextEpisode intent.
@ask.intent('WatchNextEpisode')
@preflight_check
def alexa_watch_next_episode(kodi, Show):
  return _alexa_watch_next_episode(kodi, Show)


# Handle the WatchLatestEpisode intent.
@ask.intent('WatchLatestEpisode')
@preflight_check
def alexa_watch_newest_episode(kodi, Show):
  card_title = render_template('playing_newest_episode', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    episode_id = kodi.GetNewestEpisodeFromShow(show[0][0])
    if episode_id:
      kodi.PlayEpisode(episode_id)

      episode_details = kodi.GetEpisodeDetails(episode_id)
      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode('utf-8')
      else:
        action = render_template('playing_empty').encode('utf-8')
      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=show[0][1]).encode('utf-8')
    else:
      response_text = render_template('no_new_episodes_show', show_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchLastShow intent.
@ask.intent('WatchLastShow')
@preflight_check
def alexa_watch_last_show(kodi):
  card_title = render_template('last_unwatched').encode('utf-8')
  log.info(card_title)

  last_show_obj = kodi.GetLastWatchedShow()

  try:
    last_show_id = last_show_obj['result']['episodes'][0]['tvshowid']
    next_episode_id = kodi.GetNextUnwatchedEpisode(last_show_id)

    if next_episode_id:
      kodi.PlayEpisode(next_episode_id)

      episode_details = kodi.GetEpisodeDetails(next_episode_id)
      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode('utf-8')
      else:
        action = render_template('playing_empty').encode('utf-8')
      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=last_show_obj['result']['episodes'][0]['showtitle']).encode('utf-8')
    else:
      response_text = render_template('no_new_episodes_show', show_name=last_show_obj['result']['episodes'][0]['showtitle']).encode('utf-8')
  except:
    response_text = render_template('error_parsing_results').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchRandomMusicVideo intent.
@ask.intent('WatchRandomMusicVideo')
@preflight_check
def alexa_watch_random_music_video(kodi, MusicVideoGenre, Artist):
  if MusicVideoGenre and Artist:
    card_title = render_template('playing_random_musicvideo_genre_artist', genre=MusicVideoGenre, artist=Artist).encode('utf-8')
  if MusicVideoGenre:
    card_title = render_template('playing_random_musicvideo_genre', genre=MusicVideoGenre).encode('utf-8')
  elif Artist:
    card_title = render_template('playing_random_musicvideo_artist', artist=Artist).encode('utf-8')
  else:
    card_title = render_template('playing_random_musicvideo').encode('utf-8')
  log.info(card_title)

  # Select from specified genre if specified
  genre = []
  if MusicVideoGenre:
    genre = kodi.FindVideoGenre(MusicVideoGenre, 'musicvideo')
  if genre:
    mvs = kodi.GetMusicVideosByGenre(genre[0][1])
  else:
    mvs = kodi.GetMusicVideos()

  if 'result' in mvs and 'musicvideos' in mvs['result']:
    # Narrow down by artist if specified
    if Artist:
      musicvideos_result = kodi.FilterMusicVideosByArtist(mvs['result']['musicvideos'], Artist)
    else:
      musicvideos_result = mvs['result']['musicvideos']

    if musicvideos_result:
      random_musicvideo = random.choice(musicvideos_result)
      kodi.PlayMusicVideo(random_musicvideo['musicvideoid'])

      musicvideo_details = kodi.GetMusicVideoDetails(random_musicvideo['musicvideoid'])
      response_text = render_template('playing_musicvideo', musicvideo_name=random_musicvideo['label'], artist_name=musicvideo_details['artist'][0]).encode('utf-8')
    elif genre and Artist:
      response_text = render_template('could_not_find_musicvideos_genre_artist', genre_name=genre[0][1], artist_name=Artist).encode('utf-8')
    elif MusicVideoGenre and Artist:
      response_text = render_template('could_not_find_musicvideos_genre_artist', genre_name=MusicVideoGenre, artist_name=Artist).encode('utf-8')
    elif genre:
      response_text = render_template('could_not_find_musicvideos_genre', genre_name=genre[0][1]).encode('utf-8')
    elif MusicVideoGenre:
      response_text = render_template('could_not_find_musicvideos_genre', genre_name=MusicVideoGenre).encode('utf-8')
    elif Artist:
      response_text = render_template('could_not_find_musicvideos_artist', artist_name=Artist).encode('utf-8')
    else:
      response_text = render_template('error_parsing_results').encode('utf-8')
  elif genre:
    response_text = render_template('could_not_find_musicvideos_genre', genre_name=genre[0][1]).encode('utf-8')
  elif MusicVideoGenre:
    response_text = render_template('could_not_find_musicvideos_genre', genre_name=MusicVideoGenre).encode('utf-8')
  else:
    response_text = render_template('error_parsing_results').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchMusicVideo intent.
@ask.intent('WatchMusicVideo')
@preflight_check
def alexa_watch_music_video(kodi, MusicVideo, Artist):
  card_title = render_template('playing_musicvideo_card').encode('utf-8')
  log.info(card_title)

  musicvideo = kodi.FindMusicVideo(MusicVideo, Artist)
  if musicvideo:
    kodi.PlayMusicVideo(musicvideo[0][0])

    musicvideo_details = kodi.GetMusicVideoDetails(musicvideo[0][0])
    response_text = render_template('playing_musicvideo', musicvideo_name=musicvideo[0][1], artist_name=musicvideo_details['artist'][0]).encode('utf-8')
  elif Artist:
    response_text = render_template('could_not_find_musicvideo_artist', heard_musicvideo=MusicVideo, heard_artist=Artist).encode('utf-8')
  else:
    response_text = render_template('could_not_find_musicvideo', heard_musicvideo=MusicVideo).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleMusicVideos intent.
@ask.intent('ShuffleMusicVideos')
@preflight_check
def alexa_shuffle_music_videos(kodi, MusicVideoGenre, Artist):
  if MusicVideoGenre and Artist:
    card_title = render_template('shuffling_musicvideos_genre_artist', genre=MusicVideoGenre, artist=Artist).encode('utf-8')
  elif MusicVideoGenre:
    card_title = render_template('shuffling_musicvideos_genre', genre=MusicVideoGenre).encode('utf-8')
  elif Artist:
    card_title = render_template('shuffling_musicvideos_artist', artist=Artist).encode('utf-8')
  else:
    card_title = render_template('shuffling_musicvideos').encode('utf-8')
  log.info(card_title)

  # Select from specified genre if specified
  genre = []
  if MusicVideoGenre:
    genre = kodi.FindVideoGenre(MusicVideoGenre, 'musicvideo')
  if genre:
    mvs = kodi.GetMusicVideosByGenre(genre[0][1])
  else:
    mvs = kodi.GetMusicVideos()

  if 'result' in mvs and 'musicvideos' in mvs['result']:
    # Narrow down by artist if specified
    if Artist:
      musicvideos_result = kodi.FilterMusicVideosByArtist(mvs['result']['musicvideos'], Artist)
    else:
      musicvideos_result = mvs['result']['musicvideos']

    if musicvideos_result:
      musicvideos_array = []
      for musicvideo in musicvideos_result:
        musicvideos_array.append(musicvideo['musicvideoid'])

      kodi.PlayerStop()
      kodi.ClearVideoPlaylist()
      kodi.AddMusicVideosToPlaylist(musicvideos_array, True)
      kodi.StartVideoPlaylist()

      if genre and Artist:
        response_text = render_template('shuffling_musicvideos_genre_artist', genre=genre[0][1], artist=musicvideos_result[0]['artist']).encode('utf-8')
      elif genre:
        response_text = render_template('shuffling_musicvideos_genre', genre=genre[0][1]).encode('utf-8')
      elif Artist:
        response_text = render_template('shuffling_musicvideos_artist', artist=musicvideos_result[0]['artist']).encode('utf-8')
      else:
        response_text = render_template('shuffling_musicvideos').encode('utf-8')
    elif genre and Artist:
      response_text = render_template('could_not_find_musicvideos_genre_artist', genre_name=genre[0][1], artist_name=Artist).encode('utf-8')
    elif MusicVideoGenre and Artist:
      response_text = render_template('could_not_find_musicvideos_genre_artist', genre_name=MusicVideoGenre, artist_name=Artist).encode('utf-8')
    elif genre:
      response_text = render_template('could_not_find_musicvideos_genre', genre_name=genre[0][1]).encode('utf-8')
    elif MusicVideoGenre:
      response_text = render_template('could_not_find_musicvideos_genre', genre_name=MusicVideoGenre).encode('utf-8')
    elif Artist:
      response_text = render_template('could_not_find_musicvideos_artist', artist_name=Artist).encode('utf-8')
    else:
      response_text = render_template('error_parsing_results').encode('utf-8')
  elif genre:
    response_text = render_template('could_not_find_musicvideos_genre', genre_name=genre[0][1]).encode('utf-8')
  elif MusicVideoGenre:
    response_text = render_template('could_not_find_musicvideos_genre', genre_name=MusicVideoGenre).encode('utf-8')
  else:
    response_text = render_template('error_parsing_results').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def _alexa_watch_video_playlist(kodi, VideoPlaylist, shuffle=False):
  if shuffle:
    op = render_template('shuffling_empty').encode('utf-8')
  else:
    op = render_template('playing_empty').encode('utf-8')

  card_title = render_template('action_video_playlist', action=op).encode('utf-8')
  log.info(card_title)

  playlist = kodi.FindVideoPlaylist(VideoPlaylist)
  if playlist:
    if shuffle:
      videos = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
      videos_array = []
      for video in videos:
        videos_array.append(video['file'])

      kodi.PlayerStop()
      kodi.ClearVideoPlaylist()
      kodi.AddVideosToPlaylist(videos_array, True)
      kodi.StartVideoPlaylist()
    else:
      kodi.PlayerStop()
      kodi.StartVideoPlaylist(playlist[0][0])
    response_text = render_template('playing_playlist_video', action=op, playlist_name=playlist[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find_playlist', heard_name=VideoPlaylist).encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchVideoPlaylist intent.
@ask.intent('WatchVideoPlaylist')
@preflight_check
def alexa_watch_video_playlist(kodi, VideoPlaylist):
  return _alexa_watch_video_playlist(kodi, VideoPlaylist, False)


# Handle the ShuffleVideoPlaylist intent.
@ask.intent('ShuffleVideoPlaylist')
@preflight_check
def alexa_shuffle_video_playlist(kodi, VideoPlaylist):
  return _alexa_watch_video_playlist(kodi, VideoPlaylist, True)


# Handle the ShufflePlaylist intent.
@ask.intent('ShufflePlaylist')
@preflight_check
def alexa_shuffle_playlist(kodi, VideoPlaylist, AudioPlaylist):
  heard_search = ''
  if VideoPlaylist:
    heard_search = VideoPlaylist
  elif AudioPlaylist:
    heard_search = AudioPlaylist

  card_title = render_template('shuffling_playlist', playlist_name=heard_search).encode('utf-8')
  log.info(card_title)

  if heard_search:
    playlist = kodi.FindVideoPlaylist(heard_search)
    if playlist:
      videos = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
      videos_array = []
      for video in videos:
        videos_array.append(video['file'])

      kodi.PlayerStop()
      kodi.ClearVideoPlaylist()
      kodi.AddVideosToPlaylist(videos_array, True)
      kodi.StartVideoPlaylist()
      response_text = render_template('shuffling_playlist_video', playlist_name=playlist[0][1]).encode('utf-8')
    else:
      playlist = kodi.FindAudioPlaylist(heard_search)
      if playlist:
        songs = kodi.GetPlaylistItems(playlist[0][0])['result']['files']
        songs_array = []
        for song in songs:
          songs_array.append(song['id'])

        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongsToPlaylist(songs_array, True)
        kodi.StartAudioPlaylist()
        response_text = render_template('shuffling_playlist_audio', playlist_name=playlist[0][1]).encode('utf-8')

    if not playlist:
      response_text = render_template('could_not_find_playlist', heard_name=heard_search).encode('utf-8')
  else:
    response_text = render_template('error_parsing_results').encode('utf-8')

  return statement(response_text).simple_card(card_title, response_text)


def alexa_recommend_item(kodi, item, generic_type=None):
  response_text = render_template('no_recommendations').encode('utf-8')

  if item[0] == 'movie':
    response_text = render_template('recommend_movie', movie_name=item[1]).encode('utf-8')
  elif item[0] == 'tvshow':
    response_text = render_template('recommend_show', show_name=item[1]).encode('utf-8')
  elif item[0] == 'episode':
    episode_details = kodi.GetEpisodeDetails(item[2])
    response_text = render_template('recommend_episode', season=episode_details['season'], episode=episode_details['episode'], show_name=episode_details['showtitle']).encode('utf-8')
  elif item[0] == 'musicvideo':
    musicvideo_details = kodi.GetMusicVideoDetails(item[2])
    response_text = render_template('recommend_musicvideo', musicvideo_name=item[1], artist_name=musicvideo_details['artist'][0]).encode('utf-8')
  elif item[0] == 'artist':
    response_text = render_template('recommend_artist', artist_name=item[1]).encode('utf-8')
  elif item[0] == 'album':
    album_details = kodi.GetAlbumDetails(item[2])
    response_text = render_template('recommend_album', album_name=item[1], artist_name=album_details['artist'][0]).encode('utf-8')
  elif item[0] == 'song':
    song_details = kodi.GetSongDetails(item[2])
    response_text = render_template('recommend_song', song_name=item[1], artist_name=song_details['artist'][0]).encode('utf-8')
  else:
    return statement(response_text)

  if generic_type:
    session.attributes['play_media_generic_type'] = generic_type
  session.attributes['play_media_type'] = item[0]
  session.attributes['play_media_id'] = item[2]
  session.attributes['play_media_genre'] = item[3]
  return question(response_text)


# Handle the RecommendVideo intent.
@ask.intent('RecommendVideo')
@preflight_check
def alexa_recommend_video(kodi):
  log.info('Recommending video')

  item = kodi.GetRecommendedVideoItem()
  return alexa_recommend_item(kodi, item, 'video')


# Handle the RecommendAudio intent.
@ask.intent('RecommendAudio')
@preflight_check
def alexa_recommend_audio(kodi):
  log.info('Recommending audio')

  item = kodi.GetRecommendedAudioItem()
  return alexa_recommend_item(kodi, item, 'audio')


# Handle the RecommendMovie intent.
@ask.intent('RecommendMovie')
@preflight_check
def alexa_recommend_movie(kodi, MovieGenre):
  log.info('Recommending movie')

  genre = None
  if MovieGenre:
    g = kodi.FindVideoGenre(MovieGenre)
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('movies', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendShow intent.
@ask.intent('RecommendShow')
@preflight_check
def alexa_recommend_show(kodi, ShowGenre):
  log.info('Recommending show')

  genre = None
  if ShowGenre:
    g = kodi.FindVideoGenre(ShowGenre, 'tvshow')
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('tvshows', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendEpisode intent.
@ask.intent('RecommendEpisode')
@preflight_check
def alexa_recommend_episode(kodi, ShowGenre):
  log.info('Recommending episode')

  genre = None
  if ShowGenre:
    g = kodi.FindVideoGenre(ShowGenre, 'tvshow')
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('episodes', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendMusicVideo intent.
@ask.intent('RecommendMusicVideo')
@preflight_check
def alexa_recommend_music_video(kodi, MusicVideoGenre):
  log.info('Recommending music video')

  genre = None
  if MusicVideoGenre:
    g = kodi.FindVideoGenre(MusicVideoGenre, 'musicvideo')
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('musicvideos', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendArtist intent.
@ask.intent('RecommendArtist')
@preflight_check
def alexa_recommend_artist(kodi, MusicGenre):
  log.info('Recommending artist')

  genre = None
  if MusicGenre:
    g = kodi.FindMusicGenre(MusicGenre)
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('artists', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendAlbum intent.
@ask.intent('RecommendAlbum')
@preflight_check
def alexa_recommend_album(kodi, MusicGenre):
  log.info('Recommending album')

  genre = None
  if MusicGenre:
    g = kodi.FindMusicGenre(MusicGenre)
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('albums', genre)
  return alexa_recommend_item(kodi, item)


# Handle the RecommendSong intent.
@ask.intent('RecommendSong')
@preflight_check
def alexa_recommend_song(kodi, MusicGenre):
  log.info('Recommending song')

  genre = None
  if MusicGenre:
    g = kodi.FindMusicGenre(MusicGenre)
    if g:
      genre = g[0][1]
  item = kodi.GetRecommendedItem('songs', genre)
  return alexa_recommend_item(kodi, item)


# Handle the WhatNewAlbums intent.
@ask.intent('WhatNewAlbums')
@preflight_check
def alexa_what_new_albums(kodi):
  card_title = render_template('newly_added_albums').encode('utf-8')
  log.info(card_title)

  new_albums = kodi.GetRecentlyAddedAlbums()['result']['albums']

  by_word = render_template('by')
  new_album_names = list(set([u'%s %s %s' % (x['label'], by_word, x['artist'][0]) for x in new_albums]))
  num_albums = len(new_album_names)

  if num_albums == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_albums').encode('utf-8')
  else:
    random.shuffle(new_album_names)
    limited_new_album_names = new_album_names[0:5]
    album_list = limited_new_album_names[0]
    for one_album in limited_new_album_names[1:-1]:
      album_list += u', ' + one_album
    if num_albums > 5:
      album_list += u', ' + limited_new_album_names[-1] + render_template('and_more_similar')
    elif num_albums > 1:
      album_list += render_template('and') + limited_new_album_names[-1]
    response_text = render_template('you_have_list', items=album_list).encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewMovies intent.
@ask.intent('WhatNewMovies')
@preflight_check
def alexa_what_new_movies(kodi, MovieGenre):
  new_movies = None

  # If a genre has been specified, match the genre for use in selecting random films
  if MovieGenre:
    card_title = render_template('newly_added_movies_genre', genre=MovieGenre).encode('utf-8')
    genre = kodi.FindVideoGenre(MovieGenre)
    if genre:
      new_movies = kodi.GetUnwatchedMoviesByGenre(genre[0][1])
  else:
    card_title = render_template('newly_added_movies').encode('utf-8')
    new_movies = kodi.GetUnwatchedMovies()
  log.info(card_title)

  if new_movies:
    new_movie_names = list(set([u'%s' % (x['title']) for x in new_movies]))
    num_movies = len(new_movie_names)
  else:
    num_movies = 0

  if num_movies == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_movies').encode('utf-8')
  else:
    random.shuffle(new_movie_names)
    limited_new_movie_names = new_movie_names[0:5]
    movie_list = limited_new_movie_names[0]
    for one_movie in limited_new_movie_names[1:-1]:
      movie_list += u', ' + one_movie
    if num_movies > 5:
      movie_list += u', ' + limited_new_movie_names[-1] + render_template('and_more_similar')
    elif num_movies > 1:
      movie_list += render_template('and') + limited_new_movie_names[-1]
    response_text = render_template('you_have_list', items=movie_list).encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewShows intent.
#
# Lists the shows that have had new episodes added to Kodi in the last 5 days
@ask.intent('WhatNewShows')
@preflight_check
def alexa_what_new_shows(kodi):
  card_title = render_template('newly_added_shows').encode('utf-8')
  log.info(card_title)

  new_episodes = kodi.GetUnwatchedEpisodes()

  # Find out how many EPISODES were recently added and get the names of the SHOWS
  new_show_names = list(set([u'%s' % (x['show']) for x in new_episodes]))
  num_shows = len(new_show_names)

  if num_shows == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_shows').encode('utf-8')
  elif len(new_show_names) == 1:
    # There's only one new show, so provide information about the number of episodes, too.
    count = len(new_episodes)
    if count == 1:
      response_text = render_template('one_new_episode', show_name=new_show_names[0]).encode('utf-8')
    elif count == 2:
      response_text = render_template('two_new_episodes', show_name=new_show_names[0]).encode('utf-8')
    else:
      response_text = render_template('multiple_new_episodes', show_name=new_show_names[0], count=count).encode('utf-8')
  else:
    # More than one new show has new episodes ready
    random.shuffle(new_show_names)
    limited_new_show_names = new_show_names[0:5]
    show_list = limited_new_show_names[0]
    for one_show in limited_new_show_names[1:-1]:
      show_list += u', ' + one_show
    if num_shows > 5:
      show_list += u', ' + limited_new_show_names[-1] + render_template('and_more_similar')
    elif num_shows > 1:
      show_list += render_template('and') + limited_new_show_names[-1]
    response_text = render_template('you_have_episode_list', items=show_list).encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewEpisodes intent.
@ask.intent('WhatNewEpisodes')
@preflight_check
def alexa_what_new_episodes(kodi, Show):
  card_title = render_template('looking_for_show', heard_show=Show).encode('utf-8')
  log.info(card_title)

  show = kodi.FindTvShow(Show)
  if show:
    num_unwatched = len(kodi.GetUnwatchedEpisodesFromShow(show[0][0]))

    if num_unwatched > 0:
      if num_unwatched == 1:
        response_text = render_template('one_unseen_show', show_name=show[0][1]).encode('utf-8')
      else:
        response_text = render_template('multiple_unseen_show', show_name=show[0][1], num=num_unwatched).encode('utf-8')
    else:
      response_text = render_template('no_unseen_show', show_name=show[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=Show).encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatAlbums intent.
@ask.intent('WhatAlbums')
@preflight_check
def alexa_what_albums(kodi, Artist):
  card_title = render_template('albums_by', heard_artist=Artist).encode('utf-8')
  log.info(card_title)

  artist = kodi.FindArtist(Artist)
  if artist:
    albums_result = kodi.GetArtistAlbums(artist[0][0])
    albums = albums_result['result']['albums']
    num_albums = len(albums)
    if num_albums > 0:
      really_albums = list(set([u'%s' % (x['label']) for x in albums]))
      album_list = really_albums[0]
      if num_albums > 1:
        for one_album in really_albums[1:-1]:
          album_list += u', ' + one_album
        album_list += render_template('and') + really_albums[-1]
      response_text = render_template('you_have_list', items=album_list).encode('utf-8')
    else:
      response_text = render_template('no_albums_artist', artist=artist[0][1]).encode('utf-8')
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode('utf-8')

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


def get_help_samples(limit=7):
  # read example slot values from language-specific file.
  sample_slotvals = {}
  fn = os.path.join(os.path.dirname(__file__), 'sample_slotvals.%s.txt' % (LANGUAGE))
  f = codecs.open(fn, 'rb', 'utf-8')
  for line in f:
    media_type, media_title = line.encode('utf-8').strip().split(' ', 1)
    sample_slotvals[media_type] = media_title.strip()
  f.close()

  # don't suggest utterances for the following intents, because they depend on
  # context to make any sense:
  ignore_intents = [
    'PlayerMoveUp',
    'PlayerMoveDown',
    'PlayerMoveLeft',
    'PlayerMoveRight',
    'PlayerRotateClockwise',
    'PlayerRotateCounterClockwise',
    'PlayerZoomHold',
    'PlayerZoomIn',
    'PlayerZoomInMoveUp',
    'PlayerZoomInMoveDown',
    'PlayerZoomInMoveLeft',
    'PlayerZoomInMoveRight',
    'PlayerZoomOut',
    'PlayerZoomOutMoveUp',
    'PlayerZoomOutMoveDown',
    'PlayerZoomOutMoveLeft',
    'PlayerZoomOutMoveRight',
    'PlayerZoomReset'
  ]

  # build complete list of possible utterances from file.
  utterances = {}
  fn = os.path.join(os.path.dirname(__file__), 'speech_assets/SampleUtterances.%s.txt' % (LANGUAGE))
  f = codecs.open(fn, 'rb', 'utf-8')
  for line in f:
    intent, utterance = line.encode('utf-8').strip().split(' ', 1)
    if intent in ignore_intents: continue
    if intent not in utterances:
      utterances[intent] = []
    utterances[intent].append(utterance)
  f.close()

  # pick random utterances to return, up to the specified limit.
  sample_utterances = {}
  for k in random.sample(utterances.keys(), limit):
    # substitute slot references for sample media titles.
    sample_utterances[k] = re.sub(r'{(\w+)?}', lambda m: sample_slotvals.get(m.group(1), m.group(1)), random.choice(utterances[k])).decode('utf-8')

  return sample_utterances


@ask.intent('AMAZON.HelpIntent')
@preflight_check
def prepare_help_message(kodi):
  sample_utterances = get_help_samples()

  response_text = render_template('help', example=sample_utterances.popitem()[1]).encode('utf-8')
  reprompt_text = render_template('help_short', example=sample_utterances.popitem()[1]).encode('utf-8')
  card_title = render_template('help_card').encode('utf-8')
  samples = ''
  for sample in sample_utterances.values():
    samples += '"%s"\n' % (sample)
  card_text = render_template('help_text', examples=samples).encode('utf-8')
  log.info(card_title)

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, card_text)

  return question(response_text).reprompt(reprompt_text).simple_card(card_title, card_text)


# No intents invoked
@ask.launch
def alexa_launch():
  sample_utterances = get_help_samples()

  response_text = render_template('welcome').encode('utf-8')
  reprompt_text = render_template('help_short', example=sample_utterances.popitem()[1]).encode('utf-8')
  card_title = response_text
  log.info(card_title)

  # All non-playback requests should keep the session open
  session.attributes['queries_keep_open'] = True

  return question(response_text).reprompt(reprompt_text)


@ask.session_ended
def session_ended():
  return "{}", 200


# End of intent methods
