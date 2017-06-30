import re
import string
import random
import os
from kodi_voice import KodiConfigParser, Kodi

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

kodi = Kodi(config)


def clean_results(resp, cat, key, limit=100):
  all = []
  if 'result' in resp and cat in resp['result']:
    for v in retrieved['result'][cat]:
      name = kodi.sanitize_name(v[key], normalize=False)
      # omit titles with digits, as Amazon never passes numbers as digits
      if not re.search(r'\d', name):
        all.append(name)

  cleaned = list(set(all))
  cleaned = filter(None, cleaned)
  random.shuffle(cleaned)
  cleaned = cleaned[:limit]

  return cleaned


def write_file(filename, items=[]):
  f = open(filename, 'w')
  for a in items:
    f.write("%s\n" % a.encode("utf-8"))
  f.close()


# Generate MUSICPLAYLISTS Slot
retrieved = kodi.GetMusicPlaylists()
cl = clean_results(retrieved, 'files', 'label')
write_file('MUSICPLAYLISTS', cl)


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
