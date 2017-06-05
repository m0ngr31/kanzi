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
from multiprocessing import Process
from flask import Flask, json, render_template
from flask_ask import Ask, session, question, statement, audio, request, context
from shutil import copyfile
from kodi_voice import KodiConfigParser, Kodi


app = Flask(__name__)

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

SKILL_ID = config.get('alexa', 'skill_id')
if SKILL_ID and SKILL_ID != 'None':
  app.config['ASK_APPLICATION_ID'] = SKILL_ID

LANGUAGE = config.get('global', 'language')
if LANGUAGE and LANGUAGE != 'None' and LANGUAGE == 'de':
  TEMPLATE_FILE = "templates.de.yaml"
else:
  TEMPLATE_FILE = "templates.en.yaml"

# According to this: https://alexatutorial.com/flask-ask/configuration.html
# Timestamp based verification shouldn't be used in production. Use at own risk
# app.config['ASK_VERIFY_TIMESTAMP_DEBUG'] = True

# Needs to be instanced after app is configured
ask = Ask(app, "/", None, path=TEMPLATE_FILE)


# Start of intent methods

# Handle the CurrentPlayItemInquiry intent.
@ask.intent('CurrentPlayItemInquiry')
def alexa_current_playitem_inquiry():
  card_title = render_template('current_playing_item').encode("utf-8")
  print card_title

  response_text = render_template('nothing_playing')

  kodi = Kodi(config, context)
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

  response_text = response_text.encode("utf-8")
  return statement(response_text).simple_card(card_title, response_text)


# Handle the CurrentPlayItemTimeRemaining intent.
@ask.intent('CurrentPlayItemTimeRemaining')
def alexa_current_playitem_time_remaining():
  card_title = render_template('time_left_playing').encode("utf-8")
  print card_title

  response_text = render_template('nothing_playing').encode("utf-8")

  kodi = Kodi(config, context)
  status = kodi.GetPlayerStatus()
  if status['state'] is not 'stop':
    minsleft = status['total_mins'] - status['time_mins']
    if minsleft == 0:
      response_text = render_template('remaining_close').encode("utf-8")
    elif minsleft == 1:
      response_text = render_template('remaining_min').encode("utf-8")
    elif minsleft > 1:
      response_text = render_template('remaining_mins', minutes=minsleft).encode("utf-8")
      tz = config.get(kodi.dev_cfg_section, 'timezone')
      if minsleft > 9 and tz and tz != 'None':
        utctime = datetime.datetime.now(pytz.utc)
        loctime = utctime.astimezone(pytz.timezone(tz))
        endtime = loctime + datetime.timedelta(minutes=minsleft)
        response_text += render_template('remaining_time', end_time=endtime.strftime('%I:%M')).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


def alexa_play_pause():
  card_title = render_template('play_pause').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerPlayPause()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.PauseIntent intent.
@ask.intent('AMAZON.PauseIntent')
def alexa_pause():
  return alexa_play_pause()


# Handle the AMAZON.ResumeIntent intent.
@ask.intent('AMAZON.ResumeIntent')
def alexa_resume():
  return alexa_play_pause()


def alexa_stop_cancel(kodi):
  if session.new:
    card_title = render_template('stopping').encode("utf-8")
    print card_title

    kodi.PlayerStop()
    response_text = render_template('playback_stopped').encode("utf-8")

    return statement(response_text).simple_card(card_title, response_text)
  else:
    return statement("")


# Handle the AMAZON.StopIntent intent.
@ask.intent('AMAZON.StopIntent')
def alexa_stop():
  kodi = Kodi(config, context)
  return alexa_stop_cancel(kodi)


# Handle the AMAZON.CancelIntent intent.
@ask.intent('AMAZON.CancelIntent')
def alexa_cancel():
  kodi = Kodi(config, context)
  return alexa_stop_cancel(kodi)


# Handle the AMAZON.NoIntent intent.
@ask.intent('AMAZON.NoIntent')
def alexa_no():
  kodi = Kodi(config, context)
  if 'play_media_type' in session.attributes and session.attributes['play_media_type'] != 'song':
    item = kodi.GetRecommendedItem(session.attributes['play_media_type'] + 's')
    return alexa_recommend_item(kodi, item)
  return alexa_stop_cancel(kodi)


# Handle the AMAZON.YesIntent intent.
@ask.intent('AMAZON.YesIntent')
def alexa_yes():
  card_title = None

  kodi = Kodi(config, context)

  if 'shutting_down' in session.attributes:
    quit = config.get(kodi.dev_cfg_section, 'shutdown')
    if quit and quit == 'quit':
      card_title = render_template('quitting').encode("utf-8")
      kodi.ApplicationQuit()
    else:
      card_title = render_template('shutting_down').encode("utf-8")
      kodi.SystemShutdown()
  elif 'rebooting' in session.attributes:
    card_title = render_template('rebooting').encode("utf-8")
    kodi.SystemReboot()
  elif 'hibernating' in session.attributes:
    card_title = render_template('hibernating').encode("utf-8")
    kodi.SystemHibernate()
  elif 'suspending' in session.attributes:
    card_title = render_template('suspending_system').encode("utf-8")
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
    elif media_type == 'artist':
      songs_result = kodi.GetArtistSongs(media_id)
      songs = songs_result['result']['songs']
      songs_array = []
      for song in songs:
        songs_array.append(song['songid'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      # Always shuffle when generically requesting an Artist
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
    elif media_type == 'album':
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(media_id)
      kodi.StartAudioPlaylist()
    elif media_type == 'song':
      alexa_listen_recently_added_songs()
    return statement(render_template('okay').encode("utf-8"))

  if card_title:
    print card_title
    return statement(card_title).simple_card(card_title, "")
  else:
    return statement("")


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
def alexa_player_seek_forward(ForwardDur):
  card_title = render_template('step_forward').encode("utf-8")
  print card_title

  response_text = ""

  seek_sec = duration_in_seconds(ForwardDur)
  print "Stepping forward by %d seconds" % (seek_sec)

  kodi = Kodi(config, context)
  kodi.PlayerSeek(seek_sec)

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerSeekBackward intent.
@ask.intent('PlayerSeekBackward')
def alexa_player_seek_backward(BackwardDur):
  card_title = render_template('step_backward').encode("utf-8")
  print card_title

  response_text = ""

  seek_sec = duration_in_seconds(BackwardDur)
  print "Stepping backward by %d seconds" % (seek_sec)

  kodi = Kodi(config, context)
  kodi.PlayerSeek(-seek_sec)

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerSeekSmallForward intent.
@ask.intent('PlayerSeekSmallForward')
def alexa_player_seek_smallforward():
  card_title = render_template('step_forward').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSeekSmallForward()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerSeekSmallBackward intent.
@ask.intent('PlayerSeekSmallBackward')
def alexa_player_seek_smallbackward():
  card_title = render_template('step_backward').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSeekSmallBackward()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerSeekBigForward intent.
@ask.intent('PlayerSeekBigForward')
def alexa_player_seek_bigforward():
  card_title = render_template('big_step_forward').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSeekBigForward()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerSeekBigBackward intent.
@ask.intent('PlayerSeekBigBackward')
def alexa_player_seek_bigbackward():
  card_title = render_template('big_step_backward').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSeekBigBackward()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


def find_and_play(kodi, needle, content=['video','audio'], shuffle=False, slot_hint='unknown', slot_ignore=[]):
  print 'Find and Play: "%s"' % (needle.encode("utf-8"))
  if slot_hint != 'unknown':
    print 'Pre-match with slot: ' + slot_hint
  print 'Searching content types: '
  print content

  # The order of the searches here is not random, please don't reorganize
  # without giving some thought to overall performance based on most
  # frequently requested types and user expectations.

  # Video playlist?
  if 'video' in content and 'VideoPlaylist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'VideoPlaylist'):
    playlist_id, playlist_label = kodi.FindVideoPlaylist(needle)
    if playlist_id:
      if shuffle:
        videos = kodi.GetPlaylistItems(playlist_id)['result']['files']
        videos_array = []
        for video in videos:
          videos_array.append(video['file'])

        kodi.PlayerStop()
        kodi.ClearVideoPlaylist()
        kodi.AddVideosToPlaylist(videos_array, True)
        kodi.StartVideoPlaylist()
        op = render_template('shuffling_empty').encode("utf-8")
      else:
        kodi.PlayerStop()
        kodi.StartVideoPlaylist(playlist_id)
        op = render_template('playing_empty').encode("utf-8")
      return render_template('playing_playlist_video', action=op, playlist_name=playlist_label).encode("utf-8")

  # Audio playlist?
  if 'audio' in content and 'AudioPlaylist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'AudioPlaylist'):
    playlist_id, playlist_label = kodi.FindAudioPlaylist(needle)
    if playlist_id:
      if shuffle:
        songs = kodi.GetPlaylistItems(playlist_id)['result']['files']
        songs_array = []
        for song in songs:
          songs_array.append(song['id'])

        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongsToPlaylist(songs_array, True)
        kodi.StartAudioPlaylist()
        op = render_template('shuffling_empty').encode("utf-8")
      else:
        kodi.PlayerStop()
        kodi.StartAudioPlaylist(playlist_id)
        op = render_template('playing_empty').encode("utf-8")
      return render_template('playing_playlist_audio', action=op, playlist_name=playlist_label).encode("utf-8")

  # Movie?
  if 'video' in content and 'Movie' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Movie'):
    movie_id, movie_label = kodi.FindMovie(needle)
    if movie_id:
      if kodi.GetMovieDetails(movie_id)['resume']['position'] > 0:
        action = render_template('resuming_empty').encode("utf-8")
      else:
        action = render_template('playing_empty').encode("utf-8")
      kodi.PlayMovie(movie_id)
      return render_template('playing_action', action=action, movie_name=movie_label).encode("utf-8")

  # Show?
  if 'video' in content and 'Show' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Show'):
    show_id, show_label = kodi.FindTvShow(needle)
    if show_id:
      episode_id = None
      episodes_array = []

      if shuffle:
        # Shuffle all episodes of the specified show
        episodes_result = kodi.GetEpisodesFromShow(show_id)
        for episode in episodes_result['result']['episodes']:
          episodes_array.append(episode['episodeid'])

        kodi.PlayerStop()
        kodi.ClearVideoPlaylist()
        kodi.AddEpisodesToPlaylist(episodes_array, shuffle)
        kodi.StartVideoPlaylist()
        return render_template('shuffling', heard_name=show_label).encode("utf-8")
      else:
        # Try the next unwatched episode first
        episode_id = kodi.GetNextUnwatchedEpisode(show_id)
        if not episode_id:
          # All episodes already watched, so just play a random episode
          episodes_result = kodi.GetEpisodesFromShow(show_id)
          for episode in episodes_result['result']['episodes']:
            episodes_array.append(episode['episodeid'])
          episode_id = random.choice(episodes_array)

        if episode_id:
          episode_details = kodi.GetEpisodeDetails(episode_id)
          kodi.PlayEpisode(episode_id)
          return render_template('playing_episode_number', season=episode_details['season'], episode=episode_details['episode'], show_name=show_label).encode("utf-8")

  # Artist?
  if 'audio' in content and 'Artist' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Artist'):
    artist_id, artist_label = kodi.FindArtist(needle)
    if artist_id:
      songs_result = kodi.GetArtistSongs(artist_id)
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
        op = render_template('shuffling_empty').encode("utf-8")
      else:
        op = render_template('playing_empty').encode("utf-8")
      return render_template('playing_action', action=op, movie_name=artist_label).encode("utf-8")

  # Song?
  if 'audio' in content and 'Song' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Song'):
    song_id, song_label = kodi.FindSong(needle)
    if song_id:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongToPlaylist(song_id)
      kodi.StartAudioPlaylist()
      return render_template('playing_song', song_name=song_label).encode("utf-8")

  # Album?
  if 'audio' in content and 'Album' not in slot_ignore and (slot_hint == 'unknown' or slot_hint == 'Album'):
    album_id, album_label = kodi.FindAlbum(needle)
    if album_id:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(album_id, shuffle)
      kodi.StartAudioPlaylist()
      if shuffle:
        return render_template('shuffling_album', album_name=album_label).encode("utf-8")
      else:
        return render_template('playing_album', album_name=album_label).encode("utf-8")

  return None


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
def alexa_shuffle_media(Show=None):
  kodi = Kodi(config, context)

  # Some media types don't make sense when shuffling
  ignore_slots = ['Movie', 'Song']

  card_title = render_template('shuffling', heard_name=Show).encode("utf-8")
  print card_title

  disable_ds = os.getenv('DISABLE_DEEP_SEARCH')
  if disable_ds and disable_ds != 'None':
    response_text = render_template('help_play').encode("utf-8")
  else:
    response_text = find_and_play(kodi, Show, shuffle=True, slot_hint='Show', slot_ignore=ignore_slots)
    if not response_text:
      ignore_slots.append('Show')
      response_text = find_and_play(kodi, Show, shuffle=True, slot_ignore=ignore_slots)
    if not response_text:
      response_text = render_template('could_not_find', heard_name=Show).encode("utf-8")

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
@ask.intent('PlayMedia')
def alexa_play_media(Movie=None, Artist=None, content=None, shuffle=False):
  kodi = Kodi(config, context)

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

  card_title = render_template('playing', heard_name=heard_search).encode("utf-8")
  print card_title

  if not config.getboolean('global', 'deep_search'):
    response_text = render_template('help_play').encode("utf-8")
  else:
    response_text = find_and_play(kodi, heard_search, content, shuffle, slot_hint=heard_slot)
    if not response_text and heard_slot != 'unknown':
      response_text = find_and_play(kodi, heard_search, content, shuffle, slot_ignore=[heard_slot])
    if not response_text:
      response_text = render_template('could_not_find', heard_name=heard_search).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)

# Handle the ListenToAudio intent.
#
# Defaults to Artists, but will fuzzy match across the library if none found.
@ask.intent('ListenToAudio')
def alexa_listen_audio(Artist):
  print "Listen to audio..."
  return alexa_play_media(Artist=Artist, content=['audio'])


# Handle the ListenToArtist intent (Shuffles all music by an artist).
@ask.intent('ListenToArtist')
def alexa_listen_artist(Artist):
  card_title = render_template('listen_artist', heard_artist=Artist).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  artist_id, artist_label = kodi.FindArtist(Artist)
  if artist_id:
    songs_result = kodi.GetArtistSongs(artist_id)
    songs = songs_result['result']['songs']

    songs_array = []

    for song in songs:
      songs_array.append(song['songid'])

    kodi.PlayerStop()
    kodi.ClearAudioPlaylist()
    kodi.AddSongsToPlaylist(songs_array, True)
    kodi.StartAudioPlaylist()
    response_text = render_template('playing', heard_name=artist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAlbum intent (Play whole album, or whole album by a specific artist).
@ask.intent('ListenToAlbum')
def alexa_listen_album(Album, Artist, shuffle=False):
  if shuffle:
    card_title = render_template('shuffling_album_card').encode("utf-8")
  else:
    card_title = render_template('playing_album_card').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  if Artist:
    artist_id, artist_label = kodi.FindArtist(Artist)
    if artist_id:
      albums = kodi.GetArtistAlbums(artist_id)
      if 'result' in albums and 'albums' in albums['result']:
        albums_list = albums['result']['albums']
        album_located = kodi.matchHeard(Album, albums_list, 'label')

        if album_located:
          album_id = album_located['albumid']
          album_label = album_located['label']
          kodi.PlayerStop()
          kodi.ClearAudioPlaylist()
          kodi.AddAlbumToPlaylist(album_id, shuffle)
          kodi.StartAudioPlaylist()
          if shuffle:
            response_text = render_template('shuffling_album_artist', album_name=album_label, artist=artist_label).encode("utf-8")
          else:
            response_text = render_template('playing_album_artist', album_name=album_label, artist=artist_label).encode("utf-8")
        else:
          response_text = render_template('could_not_find_album_artist', album_name=Album, artist=artist_label).encode("utf-8")
      else:
        response_text = render_template('could_not_find_album_artist', album_name=Album, artist=Artist).encode("utf-8")
    else:
      response_text = render_template('could_not_find_album_artist', album_name=Album, artist=Artist).encode("utf-8")
  else:
    album_id, album_label = kodi.FindAlbum(Album)
    if album_id:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(album_id, shuffle)
      kodi.StartAudioPlaylist()
      if shuffle:
        response_text = render_template('shuffling_album', album_name=album_label).encode("utf-8")
      else:
        response_text = render_template('playing_album', album_name=album_label).encode("utf-8")
    else:
      response_text = render_template('could_not_find_album', album_name=Album).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleAlbum intent (Shuffle whole album, or whole album by a specific artist).
@ask.intent('ShuffleAlbum')
def alexa_shuffle_album(Album, Artist):
  return alexa_listen_album(Album, Artist, True)


# Handle the ListenToLatestAlbum intent (Play latest album by a specific artist).
@ask.intent('ListenToLatestAlbum')
def alexa_listen_latest_album(Artist, shuffle=False):
  if shuffle:
    card_title = render_template('shuffling_latest_album_card', heard_artist=Artist).encode("utf-8")
  else:
    card_title = render_template('playing_latest_album_card', heard_artist=Artist).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  artist_id, artist_label = kodi.FindArtist(Artist)
  if artist_id:
    album_id = kodi.GetNewestAlbumFromArtist(artist_id)
    if album_id:
      album_label = kodi.GetAlbumDetails(album_id)['label']
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddAlbumToPlaylist(album_id, shuffle)
      kodi.StartAudioPlaylist()
      if shuffle:
        response_text = render_template('shuffling_album_artist', album_name=album_label, artist=artist_label).encode("utf-8")
      else:
        response_text = render_template('playing_album_artist', album_name=album_label, artist=artist_label).encode("utf-8")
    else:
      response_text = render_template('could_not_find_artist', artist_name=artist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleLatestAlbum intent (Shuffle latest album by a specific artist).
@ask.intent('ShuffleLatestAlbum')
def alexa_shuffle_latest_album(Artist):
  return alexa_listen_latest_album(Artist, True)


# Handle the ListenToSong intent (Play a song, or song by a specific artist).
@ask.intent('ListenToSong')
def alexa_listen_song(Song, Artist):
  card_title = render_template('playing_song_card').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  if Artist:
    artist_id, artist_label = kodi.FindArtist(Artist)
    if artist_id:
      songs = kodi.GetArtistSongs(artist_id)
      if 'result' in songs and 'songs' in songs['result']:
        songs_list = songs['result']['songs']
        song_located = kodi.matchHeard(Song, songs_list, 'label')

        if song_located:
          song_id = song_located['songid']
          song_label = song_located['label']
          kodi.PlayerStop()
          kodi.ClearAudioPlaylist()
          kodi.AddSongToPlaylist(song_id)
          kodi.StartAudioPlaylist()
          response_text = render_template('playing_song_artist', song_name=song_label, artist=artist_label).encode("utf-8")
        else:
          response_text = render_template('could_not_find_song_artist', song_name=Song, artist=artist_label).encode("utf-8")
      else:
        response_text = render_template('could_not_find_song_artist', song_name=Song, artist=Artist).encode("utf-8")
    else:
      response_text = render_template('could_not_find_song_artist', song_name=Song, artist=Artist).encode("utf-8")
  else:
    song_id, song_label = kodi.FindSong(Song)
    if song_id:
      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongToPlaylist(song_id)
      kodi.StartAudioPlaylist()
      response_text = render_template('playing_song', song_name=song_label).encode("utf-8")
    else:
      response_text = render_template('could_not_find_song', song_name=Song).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAlbumOrSong intent (Play whole album or song by a specific artist).
@ask.intent('ListenToAlbumOrSong')
def alexa_listen_album_or_song(Song, Album, Artist):
  if Song:
    heard_search = Song
  elif Album:
    heard_search = Album

  card_title = render_template('playing_album_or_song').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  artist_id, artist_label = kodi.FindArtist(Artist)
  if artist_id:
    songs = kodi.GetArtistSongs(artist_id)
    if 'result' in songs and 'songs' in songs['result']:
      songs_list = songs['result']['songs']
      song_located = kodi.matchHeard(heard_search, songs_list)

      if song_located:
        song_id = song_located['songid']
        song_label = song_located['label']
        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongToPlaylist(song_id)
        kodi.StartAudioPlaylist()
        response_text = render_template('playing_song_artist', song_name=song_label, artist=artist_label).encode("utf-8")
      else:
        albums = kodi.GetArtistAlbums(artist_id)
        if 'result' in albums and 'albums' in albums['result']:
          albums_list = albums['result']['albums']
          album_located = kodi.matchHeard(heard_search, albums_list, 'label')

          if album_located:
            album_id = album_located['albumid']
            album_label = album_located['label']
            kodi.PlayerStop()
            kodi.ClearAudioPlaylist()
            kodi.AddAlbumToPlaylist(album_id)
            kodi.StartAudioPlaylist()
            response_text = render_template('playing_album_artist', album_name=album_label, artist=artist_label).encode("utf-8")
          else:
            response_text = render_template('could_not_find_multi', heard_name=heard_search, artist=artist_label).encode("utf-8")
        else:
          response_text = render_template('could_not_find_multi', heard_name=heard_search, artist=artist_label).encode("utf-8")
    else:
      response_text = render_template('could_not_find_multi', heard_name=heard_search, artist=artist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAudioPlaylistRecent intent (Shuffle all recently added songs).
@ask.intent('ListenToAudioPlaylistRecent')
def alexa_listen_recently_added_songs():
  card_title = render_template('playing_recent_songs').encode("utf-8")
  response_text = render_template('no_recent_songs').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
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
    response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ListenToAudioPlaylist intent.
@ask.intent('ListenToAudioPlaylist')
def alexa_listen_audio_playlist(AudioPlaylist, shuffle=False):
  if shuffle:
    op = render_template('shuffling_empty').encode("utf-8")
  else:
    op = render_template('playing_empty').encode("utf-8")

  card_title = render_template('action_audio_playlist', action=op).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  playlist_id, playlist_label = kodi.FindAudioPlaylist(AudioPlaylist)
  if playlist_id:
    if shuffle:
      songs = kodi.GetPlaylistItems(playlist_id)['result']['files']
      songs_array = []
      for song in songs:
        songs_array.append(song['id'])

      kodi.PlayerStop()
      kodi.ClearAudioPlaylist()
      kodi.AddSongsToPlaylist(songs_array, True)
      kodi.StartAudioPlaylist()
    else:
      kodi.PlayerStop()
      kodi.StartAudioPlaylist(playlist_id)
    response_text = render_template('playing_playlist_audio', action=op, playlist_name=playlist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_playlist', heard_name=AudioPlaylist).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleAudioPlaylist intent.
@ask.intent('ShuffleAudioPlaylist')
def alexa_shuffle_audio_playlist(AudioPlaylist):
  return alexa_listen_audio_playlist(AudioPlaylist, True)


# Handle the PartyMode intent.
@ask.intent('PartyMode')
def alexa_party_play():
  card_title = render_template('party_mode').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerStop()
  kodi.ClearAudioPlaylist()
  kodi.PartyPlayMusic()
  response_text = render_template('playing_party').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.StartOverIntent intent.
@ask.intent('AMAZON.StartOverIntent')
def alexa_start_over():
  card_title = render_template('playing_same').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerStartOver()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.NextIntent intent.
@ask.intent('AMAZON.NextIntent')
def alexa_next():
  card_title = render_template('playing_next').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSkip()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.PreviousIntent intent.
@ask.intent('AMAZON.PreviousIntent')
def alexa_prev():
  card_title = render_template('playing_previous').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerPrev()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.ShuffleOnIntent intent.
@ask.intent('AMAZON.ShuffleOnIntent')
def alexa_shuffle_on():
  card_title = render_template('shuffle_enable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerShuffleOn()
  response_text = render_template('shuffle_on').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.ShuffleOffIntent intent.
@ask.intent('AMAZON.ShuffleOffIntent')
def alexa_shuffle_off():
  card_title = render_template('shuffle_disable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerShuffleOff()
  response_text = render_template('shuffle_off').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.LoopOnIntent intent.
@ask.intent('AMAZON.LoopOnIntent')
def alexa_loop_on():
  card_title = render_template('loop_enable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerLoopOn()
  response_text = ""
  curprops = kodi.GetActivePlayProperties()
  if curprops is not None:
    if curprops['repeat'] == 'one':
      response_text = render_template('loop_one').encode("utf-8")
    elif curprops['repeat'] == 'all':
      response_text = render_template('loop_all').encode("utf-8")
    elif curprops['repeat'] == 'off':
      response_text = render_template('loop_off').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AMAZON.LoopOffIntent intent.
@ask.intent('AMAZON.LoopOffIntent')
def alexa_loop_off():
  card_title = render_template('loop_disable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerLoopOff()
  response_text = render_template('loop_off').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the Fullscreen intent.
@ask.intent('Fullscreen')
def alexa_fullscreen():
  card_title = render_template('toggle_fullscreen').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.ToggleFullscreen()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the Mute intent.
@ask.intent('Mute')
def alexa_mute():
  card_title = render_template('mute_unmute').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.ToggleMute()
  response_text = ""

  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeUp intent.
@ask.intent('VolumeUp')
def alexa_volume_up():
  card_title = render_template('volume_up').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  vol = kodi.VolumeUp()['result']
  response_text = render_template('volume_set', num=vol).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeDown intent.
@ask.intent('VolumeDown')
def alexa_volume_down():
  card_title = render_template('volume_down').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  vol = kodi.VolumeDown()['result']
  response_text = render_template('volume_set', num=vol).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeSet intent.
@ask.intent('VolumeSet')
def alexa_volume_set(Volume):
  card_title = render_template('adjusting_volume').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  vol = kodi.VolumeSet(int(Volume), False)['result']
  response_text = render_template('volume_set', num=vol).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the VolumeSetPct intent.
@ask.intent('VolumeSetPct')
def alexa_volume_set_pct(Volume):
  card_title = render_template('adjusting_volume').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  vol = kodi.VolumeSet(int(Volume))['result']
  response_text = render_template('volume_set', num=vol).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesOn intent.
@ask.intent('SubtitlesOn')
def alexa_subtitles_on():
  card_title = render_template('subtitles_enable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSubtitlesOn()
  response_text = kodi.GetCurrentSubtitles()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesOff intent.
@ask.intent('SubtitlesOff')
def alexa_subtitles_off():
  card_title = render_template('subtitles_disable').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSubtitlesOff()
  response_text = render_template('subtitles_disable').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesNext intent.
@ask.intent('SubtitlesNext')
def alexa_subtitles_next():
  card_title = render_template('subtitles_next').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSubtitlesNext()
  response_text = kodi.GetCurrentSubtitles()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the SubtitlesPrevious intent.
@ask.intent('SubtitlesPrevious')
def alexa_subtitles_previous():
  card_title = render_template('subtitles_previous').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerSubtitlesPrevious()
  response_text = kodi.GetCurrentSubtitles()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AudioStreamNext intent.
@ask.intent('AudioStreamNext')
def alexa_audiostream_next():
  card_title = render_template('audio_stream_next').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerAudioStreamNext()
  response_text = kodi.GetCurrentAudioStream()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the AudioStreamPrevious intent.
@ask.intent('AudioStreamPrevious')
def alexa_audiostream_previous():
  card_title = render_template('audio_stream_previous').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerAudioStreamPrevious()
  response_text = kodi.GetCurrentAudioStream()

  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerMoveUp intent.
@ask.intent('PlayerMoveUp')
def alexa_player_move_up():
  card_title = render_template('player_move_up').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerMoveDown intent.
@ask.intent('PlayerMoveDown')
def alexa_player_move_down():
  card_title = render_template('player_move_down').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerMoveLeft intent.
@ask.intent('PlayerMoveLeft')
def alexa_player_move_left():
  card_title = render_template('player_move_left').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerMoveRight intent.
@ask.intent('PlayerMoveRight')
def alexa_player_move_right():
  card_title = render_template('player_move_right').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerRotateClockwise intent.
@ask.intent('PlayerRotateClockwise')
def alexa_player_rotate_clockwise():
  card_title = render_template('player_rotate').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerRotateClockwise()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerRotateCounterClockwise intent.
@ask.intent('PlayerRotateCounterClockwise')
def alexa_player_rotate_counterclockwise():
  card_title = render_template('player_rotate_cc').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerRotateCounterClockwise()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomHold intent.
@ask.intent('PlayerZoomHold')
def alexa_player_zoom_hold():
  card_title = render_template('player_zoom_hold').encode("utf-8")
  print card_title

  response_text = ""
  return statement(response_text).simple_card(card_title, response_text)


# Handle the PlayerZoomIn intent.
@ask.intent('PlayerZoomIn')
def alexa_player_zoom_in():
  card_title = render_template('player_zoom_in').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomIn()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomInMoveUp intent.
@ask.intent('PlayerZoomInMoveUp')
def alexa_player_zoom_in_move_up():
  card_title = render_template('player_zoom_in_up').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomIn()
  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomInMoveDown intent.
@ask.intent('PlayerZoomInMoveDown')
def alexa_player_zoom_in_move_down():
  card_title = render_template('player_zoom_in_down').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomIn()
  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomInMoveLeft intent.
@ask.intent('PlayerZoomInMoveLeft')
def alexa_player_zoom_in_move_left():
  card_title = render_template('player_zoom_in_left').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomIn()
  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomInMoveRight intent.
@ask.intent('PlayerZoomInMoveRight')
def alexa_player_zoom_in_move_right():
  card_title = render_template('player_zoom_in_right').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomIn()
  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomOut intent.
@ask.intent('PlayerZoomOut')
def alexa_player_zoom_out():
  card_title = render_template('player_zoom_out').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomOut()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomOutMoveUp intent.
@ask.intent('PlayerZoomOutMoveUp')
def alexa_player_zoom_out_move_up():
  card_title = render_template('player_zoom_out_up').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomOut()
  kodi.PlayerMoveUp()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomOutMoveDown intent.
@ask.intent('PlayerZoomOutMoveDown')
def alexa_player_zoom_out_move_down():
  card_title = render_template('player_zoom_out_down').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomOut()
  kodi.PlayerMoveDown()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomOutMoveLeft intent.
@ask.intent('PlayerZoomOutMoveLeft')
def alexa_player_zoom_out_move_left():
  card_title = render_template('player_zoom_out_left').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomOut()
  kodi.PlayerMoveLeft()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomOutMoveRight intent.
@ask.intent('PlayerZoomOutMoveRight')
def alexa_player_zoom_out_move_right():
  card_title = render_template('player_zoom_out_right').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoomOut()
  kodi.PlayerMoveRight()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PlayerZoomReset intent.
@ask.intent('PlayerZoomReset')
def alexa_player_zoom_reset():
  card_title = render_template('player_zoom_normal').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.PlayerZoom(1)
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Menu intent.
@ask.intent('Menu')
def alexa_context_menu():
  print 'Navigate: Context Menu'

  kodi = Kodi(config, context)
  kodi.Menu()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Home intent.
@ask.intent('Home')
def alexa_go_home():
  print 'Navigate: Home'

  kodi = Kodi(config, context)
  kodi.Home()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Select intent.
@ask.intent('Select')
def alexa_select():
  print 'Navigate: Select'

  kodi = Kodi(config, context)
  kodi.Select()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PageUp intent.
@ask.intent('PageUp')
def alexa_pageup():
  print 'Navigate: Page up'

  kodi = Kodi(config, context)
  kodi.PageUp()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the PageDown intent.
@ask.intent('PageDown')
def alexa_pagedown():
  print 'Navigate: Page down'

  kodi = Kodi(config, context)
  kodi.PageDown()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Left intent.
@ask.intent('Left')
def alexa_left():
  print 'Navigate: Left'

  kodi = Kodi(config, context)
  kodi.Left()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Right intent.
@ask.intent('Right')
def alexa_right():
  print 'Navigate: Right'

  kodi = Kodi(config, context)
  kodi.Right()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Up intent.
@ask.intent('Up')
def alexa_up():
  print 'Navigate: Up'

  kodi = Kodi(config, context)
  kodi.Up()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Down intent.
@ask.intent('Down')
def alexa_down():
  print 'Navigate: Down'

  kodi = Kodi(config, context)
  kodi.Down()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Back intent.
@ask.intent('Back')
def alexa_back():
  print 'Navigate: Back'

  kodi = Kodi(config, context)
  kodi.Back()
  response_text = render_template('short_confirm').encode("utf-8")
  return question(response_text)


# Handle the Shutdown intent.
@ask.intent('Shutdown')
def alexa_shutdown():
  response_text = render_template('are_you_sure').encode("utf-8")
  session.attributes['shutting_down'] = True
  return question(response_text).reprompt(response_text)


# Handle the Reboot intent.
@ask.intent('Reboot')
def alexa_reboot():
  response_text = render_template('are_you_sure').encode("utf-8")
  session.attributes['rebooting'] = True
  return question(response_text).reprompt(response_text)


# Handle the Hibernate intent.
@ask.intent('Hibernate')
def alexa_hibernate():
  response_text = render_template('are_you_sure').encode("utf-8")
  session.attributes['hibernating'] = True
  return question(response_text).reprompt(response_text)


# Handle the Suspend intent.
@ask.intent('Suspend')
def alexa_suspend():
  response_text = render_template('are_you_sure').encode("utf-8")
  session.attributes['suspending'] = True
  return question(response_text).reprompt(response_text)


# Handle the EjectMedia intent.
@ask.intent('EjectMedia')
def alexa_ejectmedia():
  card_title = render_template('ejecting_media').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  kodi.SystemEjectMedia()

  if not 'queries_keep_open' in session.attributes:
    return statement(card_title).simple_card(card_title, '')

  return question(card_title)


# Handle the CleanVideo intent.
@ask.intent('CleanVideo')
def alexa_clean_video():
  card_title = render_template('clean_video').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  # Use threading to prevent timeouts
  c = Process(target=kodi.CleanVideo)
  c.daemon = True
  c.start()

  time.sleep(2)

  return statement(card_title).simple_card(card_title, "")


# Handle the UpdateVideo intent.
@ask.intent('UpdateVideo')
def alexa_update_video():
  card_title = render_template('update_video').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  # Use threading to prevent timeouts
  c = Process(target=kodi.UpdateVideo)
  c.daemon = True
  c.start()

  time.sleep(2)

  return statement(card_title).simple_card(card_title, "")


# Handle the CleanAudio intent.
@ask.intent('CleanAudio')
def alexa_clean_audio():
  card_title = render_template('clean_audio').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  # Use threading to prevent timeouts
  c = Process(target=kodi.CleanMusic)
  c.daemon = True
  c.start()

  time.sleep(2)

  return statement(card_title).simple_card(card_title, "")


# Handle the UpdateAudio intent.
@ask.intent('UpdateAudio')
def alexa_update_audio():
  card_title = render_template('update_audio').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  # Use threading to prevent timeouts
  c = Process(target=kodi.UpdateMusic)
  c.daemon = True
  c.start()

  time.sleep(2)

  return statement(card_title).simple_card(card_title, "")


# Handle the AddonExecute intent.
@ask.intent('AddonExecute')
def alexa_addon_execute(Addon):
  card_title = render_template('open_addon').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  for content in ['video', 'audio', 'image', 'executable']:
    addons = kodi.GetAddons(content)
    if 'result' in addons and 'addons' in addons['result']:
      addons_array = addons['result']['addons']

      located = kodi.matchHeard(Addon, addons_array, 'name')

      if located:
        kodi.Home()
        kodi.AddonExecute(located['addonid'])
        response_text = render_template('opening', heard_name=located['name']).encode("utf-8")
        return statement(response_text).simple_card(card_title, response_text)
      else:
        response_text = render_template('could_not_find_addon', heard_addon=Addon).encode("utf-8")
    else:
      response_text = render_template('error_parsing_results').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)

# Handle the AddonGlobalSearch intent.
@ask.intent('AddonGlobalSearch')
def alexa_addon_globalsearch(Movie, Show, Artist, Album, Song):
  card_title = render_template('search').encode("utf-8")
  print card_title
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

  if (len(heard_search) > 0):
    response_text = render_template('searching', heard_name=heard_search).encode("utf-8")

    kodi = Kodi(config, context)
    kodi.Home()
    kodi.AddonGlobalSearch(heard_search)
  else:
    response_text = render_template('could_not_find_generic').encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text).reprompt(response_text)


# Handle the WatchVideo intent.
#
# Defaults to Movies, but will fuzzy match across the library if none found.
@ask.intent('WatchVideo')
def alexa_watch_video(Movie):
  print "Watch a video..."
  return alexa_play_media(Movie=Movie, content=['video'])


# Handle the WatchRandomMovie intent.
@ask.intent('WatchRandomMovie')
def alexa_watch_random_movie(Genre):
  kodi = Kodi(config, context)
  genre_located = None
  # If a genre has been specified, match the genre for use in selecting a random film
  if Genre:
    card_title = render_template('playing_random_movie_genre', genre=Genre).encode("utf-8")
    genres = kodi.GetMovieGenres()
    if 'result' in genres and 'genres' in genres['result']:
      genres_list = genres['result']['genres']
      genre_located = kodi.matchHeard(Genre, genres_list)
  else:
    card_title = render_template('playing_random_movie').encode("utf-8")
  print card_title

  # Select from specified genre if one was matched
  if genre_located:
    movies_array = kodi.GetUnwatchedMoviesByGenre(genre_located['label'])
  else:
    movies_array = kodi.GetUnwatchedMovies()
  if not len(movies_array):
    # Fall back to all movies if no unwatched available
    if genre_located:
      movies = kodi.GetMoviesByGenre(genre_located['label'])
    else:
      movies = kodi.GetMovies()
    if 'result' in movies and 'movies' in movies['result']:
      movies_array = movies['result']['movies']

  if len(movies_array):
    random_movie = random.choice(movies_array)

    kodi.PlayMovie(random_movie['movieid'], False)
    if genre_located:
      response_text = render_template('playing_genre', genre=genre_located['label'], movie_name=random_movie['label']).encode("utf-8")
    else:
      response_text = render_template('playing', heard_name=random_movie['label']).encode("utf-8")
  else:
    response_text = render_template('error_parsing_results').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchMovie intent.
@ask.intent('WatchMovie')
def alexa_watch_movie(Movie):
  card_title = render_template('playing_movie').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  movie_id, movie_label = kodi.FindMovie(Movie)
  if movie_id:
    if kodi.GetMovieDetails(movie_id)['resume']['position'] > 0:
      action = render_template('resuming_empty').encode("utf-8")
    else:
      action = render_template('playing_empty').encode("utf-8")

    kodi.PlayMovie(movie_id)
    response_text = render_template('playing_action', action=action, movie_name=movie_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_movie', heard_movie=Movie).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleShow intent.
@ask.intent('ShuffleShow')
def alexa_shuffle_show(Show):
  card_title = render_template('shuffling_episodes', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    episodes_array = []
    episodes_result = kodi.GetEpisodesFromShow(show_id)
    for episode in episodes_result['result']['episodes']:
      episodes_array.append(episode['episodeid'])

    kodi.PlayerStop()
    kodi.ClearVideoPlaylist()
    kodi.AddEpisodesToPlaylist(episodes_array, True)
    kodi.StartVideoPlaylist()
    response_text = render_template('shuffling', heard_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchRandomEpisode intent.
@ask.intent('WatchRandomEpisode')
def alexa_watch_random_episode(Show):
  card_title = render_template('playing_random_episode', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    episodes_result = kodi.GetUnwatchedEpisodesFromShow(show_id)

    if not 'episodes' in episodes_result['result']:
      # Fall back to all episodes if no unwatched available
      episodes_result = kodi.GetEpisodesFromShow(show_id)

    episodes_array = []

    for episode in episodes_result['result']['episodes']:
      episodes_array.append(episode['episodeid'])

    episode_id = random.choice(episodes_array)
    episode_details = kodi.GetEpisodeDetails(episode_id)

    kodi.PlayEpisode(episode_id, False)

    response_text = render_template('playing_episode_number', season=episode_details['season'], episode=episode_details['episode'], show_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchEpisode intent.
@ask.intent('WatchEpisode')
def alexa_watch_episode(Show, Season, Episode):
  card_title = render_template('playing_an_episode', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    episode_id = kodi.GetSpecificEpisode(show_id, Season, Episode)
    if episode_id:
      if kodi.GetEpisodeDetails(episode_id)['resume']['position'] > 0:
        action = render_template('resuming_empty').encode("utf-8")
      else:
        action = render_template('playing_empty').encode("utf-8")

      kodi.PlayEpisode(episode_id)

      response_text = render_template('playing_action_episode_number', action=action, season=Season, episode=Episode, show_name=show_label).encode("utf-8")

    else:
      response_text = render_template('could_not_find_episode_show', season=Season, episode=Episode, show_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchNextEpisode intent.
@ask.intent('WatchNextEpisode')
def alexa_watch_next_episode(Show):
  card_title = render_template('playing_next_unwatched_episode', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    next_episode_id = kodi.GetNextUnwatchedEpisode(show_id)
    if next_episode_id:
      episode_details = kodi.GetEpisodeDetails(next_episode_id)

      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode("utf-8")
      else:
        action = render_template('playing_empty').encode("utf-8")

      kodi.PlayEpisode(next_episode_id)

      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=show_label).encode("utf-8")
    else:
      response_text = render_template('no_new_episodes_show', show_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchLatestEpisode intent.
@ask.intent('WatchLatestEpisode')
def alexa_watch_newest_episode(Show):
  card_title = render_template('playing_newest_episode', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    episode_id = kodi.GetNewestEpisodeFromShow(show_id)
    if episode_id:
      episode_details = kodi.GetEpisodeDetails(episode_id)

      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode("utf-8")
      else:
        action = render_template('playing_empty').encode("utf-8")

      kodi.PlayEpisode(episode_id)

      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=show_label).encode("utf-8")
    else:
      response_text = render_template('no_new_episodes_show', show_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_show', heard_show=Show).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchLastShow intent.
@ask.intent('WatchLastShow')
def alexa_watch_last_show():
  card_title = render_template('last_unwatched').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  last_show_obj = kodi.GetLastWatchedShow()

  try:
    last_show_id = last_show_obj['result']['episodes'][0]['tvshowid']
    next_episode_id = kodi.GetNextUnwatchedEpisode(last_show_id)

    if next_episode_id:
      episode_details = kodi.GetEpisodeDetails(next_episode_id)

      if episode_details['resume']['position'] > 0:
        action = render_template('resuming_empty').encode("utf-8")
      else:
        action = render_template('playing_empty').encode("utf-8")

      kodi.PlayEpisode(next_episode_id)

      response_text = render_template('playing_action_episode_number', action=action, season=episode_details['season'], episode=episode_details['episode'], show_name=last_show_obj['result']['episodes'][0]['showtitle']).encode("utf-8")
    else:
      response_text = render_template('no_new_episodes_show', show_name=last_show_obj['result']['episodes'][0]['showtitle']).encode("utf-8")
  except:
    response_text = render_template('error_parsing_results').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the WatchVideoPlaylist intent.
@ask.intent('WatchVideoPlaylist')
def alexa_watch_video_playlist(VideoPlaylist, shuffle=False):
  if shuffle:
    op = render_template('shuffling_empty').encode("utf-8")
  else:
    op = render_template('playing_empty').encode("utf-8")

  card_title = render_template('action_video_playlist', action=op).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  playlist_id, playlist_label = kodi.FindVideoPlaylist(VideoPlaylist)
  if playlist_id:
    if shuffle:
      videos = kodi.GetPlaylistItems(playlist_id)['result']['files']
      videos_array = []
      for video in videos:
        videos_array.append(video['file'])

      kodi.PlayerStop()
      kodi.ClearVideoPlaylist()
      kodi.AddVideosToPlaylist(videos_array, True)
      kodi.StartVideoPlaylist()
    else:
      kodi.PlayerStop()
      kodi.StartVideoPlaylist(playlist_id)
    response_text = render_template('playing_playlist_video', action=op, playlist_name=playlist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find_playlist', heard_name=VideoPlaylist).encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


# Handle the ShuffleVideoPlaylist intent.
@ask.intent('ShuffleVideoPlaylist')
def alexa_shuffle_video_playlist(VideoPlaylist):
  return alexa_watch_video_playlist(VideoPlaylist, True)


# Handle the ShufflePlaylist intent.
@ask.intent('ShufflePlaylist')
def alexa_shuffle_playlist(VideoPlaylist, AudioPlaylist):
  heard_search = ''
  if VideoPlaylist:
    heard_search = VideoPlaylist
  elif AudioPlaylist:
    heard_search = AudioPlaylist

  card_title = render_template('shuffling_playlist', playlist_name=heard_search).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  if (len(heard_search) > 0):
    playlist_id, playlist_label = kodi.FindVideoPlaylist(heard_search)
    if playlist_id:
      videos = kodi.GetPlaylistItems(playlist_id)['result']['files']
      videos_array = []
      for video in videos:
        videos_array.append(video['file'])

      kodi.PlayerStop()
      kodi.ClearVideoPlaylist()
      kodi.AddVideosToPlaylist(videos_array, True)
      kodi.StartVideoPlaylist()
      response_text = render_template('shuffling_playlist_video', playlist_name=playlist_label).encode("utf-8")
    else:
      playlist_id, playlist_label = kodi.FindAudioPlaylist(heard_search)
      if playlist_id:
        songs = kodi.GetPlaylistItems(playlist_id)['result']['files']
        songs_array = []
        for song in songs:
          songs_array.append(song['id'])

        kodi.PlayerStop()
        kodi.ClearAudioPlaylist()
        kodi.AddSongsToPlaylist(songs_array, True)
        kodi.StartAudioPlaylist()
        response_text = render_template('shuffling_playlist_audio', playlist_name=playlist_label).encode("utf-8")

    if not playlist_id:
      response_text = render_template('could_not_find_playlist', heard_name=heard_search).encode("utf-8")
  else:
    response_text = render_template('error_parsing_results').encode("utf-8")

  return statement(response_text).simple_card(card_title, response_text)


def alexa_recommend_item(kodi, item=None):
  response_text = render_template('no_recommendations').encode("utf-8")

  if item[0] == 'movie':
    response_text = render_template('recommend_movie', movie_name=item[1]).encode("utf-8")
  elif item[0] == 'tvshow':
    response_text = render_template('recommend_show', show_name=item[1]).encode("utf-8")
  elif item[0] == 'episode':
    episode_details = kodi.GetEpisodeDetails(item[2])
    response_text = render_template('recommend_episode', season=episode_details['season'], episode=episode_details['episode'], show_name=episode_details['showtitle']).encode("utf-8")
  elif item[0] == 'musicvideo':
    musicvideo_details = kodi.GetMusicVideoDetails(item[2])
    response_text = render_template('recommend_musicvideo', musicvideo_name=item[1], artist_name=musicvideo_details['artist'][0]).encode("utf-8")
  elif item[0] == 'artist':
    response_text = render_template('recommend_artist', artist_name=item[1]).encode("utf-8")
  elif item[0] == 'album':
    album_details = kodi.GetAlbumDetails(item[2])
    response_text = render_template('recommend_album', album_name=item[1], artist_name=album_details['artist'][0]).encode("utf-8")
  elif item[0] == 'song':
    # XXX script.skin.helper doesn't return any recommended songs atm,
    # so just offer to play recently added songs
    response_text = render_template('recommend_song').encode("utf-8")

  session.attributes['play_media_type'] = item[0]
  session.attributes['play_media_id'] = item[2]
  return question(response_text)


# Handle the RecommendMedia intent.
@ask.intent('RecommendMedia')
def alexa_recommend_media():
  print "Recommending media"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem()
  return alexa_recommend_item(kodi, item)


# Handle the RecommendMovie intent.
@ask.intent('RecommendMovie')
def alexa_recommend_movie():
  print "Recommending movie"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('movies')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendShow intent.
@ask.intent('RecommendShow')
def alexa_recommend_show():
  print "Recommending show"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('tvshows')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendEpisode intent.
@ask.intent('RecommendEpisode')
def alexa_recommend_episode():
  print "Recommending episode"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('episodes')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendMusicVideo intent.
@ask.intent('RecommendMusicVideo')
def alexa_recommend_music_video():
  print "Recommending music video"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('musicvideos')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendArtist intent.
@ask.intent('RecommendArtist')
def alexa_recommend_artist():
  print "Recommending artist"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('artists')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendAlbum intent.
@ask.intent('RecommendAlbum')
def alexa_recommend_album():
  print "Recommending album"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('albums')
  return alexa_recommend_item(kodi, item)


# Handle the RecommendSong intent.
@ask.intent('RecommendSong')
def alexa_recommend_song():
  print "Recommending song"
  kodi = Kodi(config, context)
  item = kodi.GetRecommendedItem('songs')
  return alexa_recommend_item(kodi, item)


# Handle the WhatNewAlbums intent.
@ask.intent('WhatNewAlbums')
def alexa_what_new_albums():
  card_title = render_template('newly_added_albums').encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  # Get the list of recently added albums from Kodi
  new_albums = kodi.GetRecentlyAddedAlbums()['result']['albums']

  by_word = render_template('by')
  new_album_names = list(set([u'%s %s %s' % (x['label'], by_word, x['artist'][0]) for x in new_albums]))
  num_albums = len(new_album_names)

  if num_albums == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_albums').encode("utf-8")
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
    response_text = render_template('you_have_list', items=album_list).encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewMovies intent.
@ask.intent('WhatNewMovies')
def alexa_what_new_movies(Genre):
  kodi = Kodi(config, context)

  genre_located = None
  new_movies = None

  # If a genre has been specified, match the genre for use in selecting random films
  if Genre:
    card_title = render_template('newly_added_movies_genre', genre=Genre).encode("utf-8")
    genres = kodi.GetMovieGenres()
    if 'result' in genres and 'genres' in genres['result']:
      genres_list = genres['result']['genres']
      genre_located = kodi.matchHeard(Genre, genres_list)
      if genre_located:
        new_movies = kodi.GetUnwatchedMoviesByGenre(genre_located['label'])
  else:
    card_title = render_template('newly_added_movies').encode("utf-8")
    new_movies = kodi.GetUnwatchedMovies()
  print card_title

  if new_movies:
    new_movie_names = list(set([u'%s' % (x['title']) for x in new_movies]))
    num_movies = len(new_movie_names)
  else:
    num_movies = 0

  if num_movies == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_movies').encode("utf-8")
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
    response_text = render_template('you_have_list', items=movie_list).encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewShows intent.
@ask.intent('WhatNewShows')
def alexa_what_new_episodes():
  card_title = render_template('newly_added_shows').encode("utf-8")
  print card_title

  # Lists the shows that have had new episodes added to Kodi in the last 5 days

  # Get the list of unwatched EPISODES from Kodi
  kodi = Kodi(config, context)
  new_episodes = kodi.GetUnwatchedEpisodes()

  # Find out how many EPISODES were recently added and get the names of the SHOWS
  new_show_names = list(set([u'%s' % (x['show']) for x in new_episodes]))
  num_shows = len(new_show_names)

  if num_shows == 0:
    # There's been nothing added to Kodi recently
    response_text = render_template('no_new_shows').encode("utf-8")
  elif len(new_show_names) == 1:
    # There's only one new show, so provide information about the number of episodes, too.
    count = len(new_episodes)
    if count == 1:
      response_text = render_template('one_new_episode', show_name=new_show_names[0]).encode("utf-8")
    elif count == 2:
      response_text = render_template('two_new_episodes', show_name=new_show_names[0]).encode("utf-8")
    else:
      response_text = render_template('multiple_new_episodes', show_name=new_show_names[0], count=count).encode("utf-8")
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
    response_text = render_template('you_have_episode_list', items=show_list).encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatNewEpisodes intent.
@ask.intent('WhatNewEpisodes')
def alexa_what_new_episodes(Show):
  card_title = render_template('looking_for_show', heard_show=Show).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  show_id, show_label = kodi.FindTvShow(Show)
  if show_id:
    episodes_result = kodi.GetUnwatchedEpisodesFromShow(show_id)

    if not 'episodes' in episodes_result['result']:
      num_of_unwatched = 0
    else:
      num_of_unwatched = len(episodes_result['result']['episodes'])

    if num_of_unwatched > 0:
      if num_of_unwatched == 1:
        response_text = render_template('one_unseen_show', show_name=show_label).encode("utf-8")
      else:
        response_text = render_template('multiple_unseen_show', show_name=show_label, num=num_of_unwatched).encode("utf-8")
    else:
      response_text = render_template('no_unseen_show', show_name=show_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find', heard_name=Show).encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


# Handle the WhatAlbums intent.
@ask.intent('WhatAlbums')
def alexa_what_albums(Artist):
  card_title = render_template('albums_by', heard_artist=Artist).encode("utf-8")
  print card_title

  kodi = Kodi(config, context)
  artist_id, artist_label = kodi.FindArtist(Artist)
  if artist_id:
    albums_result = kodi.GetArtistAlbums(artist_id)
    albums = albums_result['result']['albums']
    num_albums = len(albums)

    if num_albums > 0:
      really_albums = list(set([u'%s' % (x['label']) for x in albums]))
      album_list = really_albums[0]
      if num_albums > 1:
        for one_album in really_albums[1:-1]:
          album_list += u', ' + one_album
        album_list += render_template('and') + really_albums[-1]
      response_text = render_template('you_have_list', items=album_list).encode("utf-8")
    else:
      response_text = render_template('no_albums_artist', artist=artist_label).encode("utf-8")
  else:
    response_text = render_template('could_not_find', heard_name=Artist).encode("utf-8")

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text)


@ask.intent('AMAZON.HelpIntent')
def prepare_help_message():
  response_text = render_template('help').encode("utf-8")
  reprompt_text = render_template('what_to_do').encode("utf-8")
  card_title = render_template('help_card').encode("utf-8")
  print card_title

  if not 'queries_keep_open' in session.attributes:
    return statement(response_text).simple_card(card_title, response_text)

  return question(response_text).reprompt(reprompt_text)


# No intents invoked
@ask.launch
def alexa_launch():
  response_text = render_template('welcome').encode("utf-8")
  reprompt_text = render_template('what_to_do').encode("utf-8")
  card_title = response_text
  print card_title

  # All non-playback requests should keep the session open
  session.attributes['queries_keep_open'] = True

  return question(response_text).reprompt(reprompt_text)


@ask.session_ended
def session_ended():
  return "", 200


# End of intent methods
