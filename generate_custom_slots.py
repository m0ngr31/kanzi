import re
import string
import random
import os
from kodi_voice import KodiConfigParser, Kodi

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

kodi = Kodi(config)


def most_words(l=[]):
  longest = 0
  for s in l:
    if len(s.split()) > longest:
      longest = len(s.split())
  return longest


def sort_by_words(l, longest):
  distributed = []
  for i in range(1, longest + 1):
    dl = [s for s in l if len(s.split()) == i]
    if len(dl) > 0:
      distributed.append(dl)
  return distributed


def clean_results(resp, cat, key, limit=None):
  if not limit:
    try:
      limit = kodi.config.get('alexa', 'slot_items_max')
      if limit and limit != 'None':
        limit = int(limit)
      else:
        limit = None
    except:
      limit = None
  if not limit:
    limit = 100

  cleaned = []
  if 'result' in resp and cat in resp['result']:
    for v in retrieved['result'][cat]:
      name = kodi.sanitize_name(v[key], normalize=False)
      # omit titles with digits, as Amazon never passes numbers as digits
      if not re.search(r'\d', name):
        cleaned.append(name)

  cleaned = {v.lower(): v for v in cleaned}.values()
  cleaned = filter(None, cleaned)
  random.shuffle(cleaned)

  # distribute strings evenly by number of words
  if len(cleaned) > limit:
    longest = most_words(cleaned)
    distributed = sort_by_words(cleaned, longest)
    if len(distributed) > 0:
      total = 0
      cleaned = []
      while total < limit:
        for l in distributed:
          if len(l) > 0:
            total += 1
            cleaned.append(l.pop())

  # sort by number of words just for visibility
  if len(cleaned) > 0:
    longest = most_words(cleaned)
    distributed = sort_by_words(cleaned, longest)
    if len(distributed) > 0:
      cleaned = []
      for dl in distributed:
        cleaned += [l for l in dl]

  return cleaned[:limit]


def write_file(filename, items=[]):
  print 'Writing: %s' % (filename)
  f = open(filename, 'w')
  for a in items:
    f.write("%s\n" % a.encode("utf-8"))
  f.close()


# Generate MUSICPLAYLISTS Slot
retrieved = kodi.GetMusicPlaylists()
cl = clean_results(retrieved, 'files', 'label')
write_file('MUSICPLAYLISTS', cl)


# Generate MUSICGENRES Slot
retrieved = kodi.GetMusicGenres()
cl = clean_results(retrieved, 'genres', 'label')
write_file('MUSICGENRES', cl)


# Generate MUSICARTISTS Slot
retrieved = kodi.GetMusicArtists()
cl = clean_results(retrieved, 'artists', 'artist')
write_file('MUSICARTISTS', cl)


# Generate MUSICALBUMS Slot
retrieved = kodi.GetAlbums()
cl = clean_results(retrieved, 'albums', 'label')
write_file('MUSICALBUMS', cl)


# Generate MUSICSONGS Slot
retrieved = kodi.GetSongs()
cl = clean_results(retrieved, 'songs', 'label')
write_file('MUSICSONGS', cl)


# Generate VIDEOPLAYLISTS Slot
retrieved = kodi.GetVideoPlaylists()
cl = clean_results(retrieved, 'files', 'label')
write_file('VIDEOPLAYLISTS', cl)


# Generate MOVIEGENRES Slot
retrieved = kodi.GetVideoGenres()
cl = clean_results(retrieved, 'genres', 'label')
write_file('MOVIEGENRES', cl)


# Generate SHOWGENRES Slot
retrieved = kodi.GetVideoGenres('tvshow')
cl = clean_results(retrieved, 'genres', 'label')
write_file('SHOWGENRES', cl)


# Generate MUSICVIDEOGENRES Slot
retrieved = kodi.GetVideoGenres('musicvideo')
cl = clean_results(retrieved, 'genres', 'label')
write_file('MUSICVIDEOGENRES', cl)


# Generate MOVIES Slot
retrieved = kodi.GetMovies()
cl = clean_results(retrieved, 'movies', 'label')
write_file('MOVIES', cl)


# Generate SHOWS Slot
retrieved = kodi.GetTvShows()
cl = clean_results(retrieved, 'tvshows', 'label')
write_file('SHOWS', cl)


# Generate ADDONS Slot
retrieved = {'result': {'addons': []}}
for content in ['video', 'audio', 'image', 'executable']:
  r = kodi.GetAddons(content)
  if 'result' in r and 'addons' in r['result']:
    retrieved['result']['addons'] += r['result']['addons']
cl = clean_results(retrieved, 'addons', 'name')
write_file('ADDONS', cl)
