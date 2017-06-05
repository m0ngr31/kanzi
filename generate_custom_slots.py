import re
import string
import random
import os
from kodi_voice import KodiConfigParser, Kodi

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

kodi = Kodi(config)

# Generate MUSICARTISTS Slot
retrieved = kodi.GetMusicArtists()

all = []

if 'result' in retrieved and 'artists' in retrieved['result']:
  for v in retrieved['result']['artists']:
    name = kodi.sanitize_name(v['artist'], normalize=False)
    name_stripped = kodi.sanitize_name(v['artist'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MUSICARTISTS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate MUSICALBUMS Slot
retrieved = kodi.GetAlbums()

all = []

if 'result' in retrieved and 'albums' in retrieved['result']:
  for v in retrieved['result']['albums']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MUSICALBUMS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate MUSICSONGS Slot
retrieved = kodi.GetSongs()

all = []

if 'result' in retrieved and 'songs' in retrieved['result']:
  for v in retrieved['result']['songs']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MUSICSONGS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate MUSICPLAYLISTS Slot
retrieved = kodi.GetMusicPlaylists()

all = []

if 'result' in retrieved and 'files' in retrieved['result']:
  for v in retrieved['result']['files']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MUSICPLAYLISTS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate VIDEOPLAYLISTS Slot
retrieved = kodi.GetVideoPlaylists()

all = []

if 'result' in retrieved and 'files' in retrieved['result']:
  for v in retrieved['result']['files']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('VIDEOPLAYLISTS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate MOVIEGENRES Slot
retrieved = kodi.GetMovieGenres()

all = []

if 'result' in retrieved and 'genres' in retrieved['result']:
  for v in retrieved['result']['genres']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MOVIEGENRES', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate MOVIES Slot
retrieved = kodi.GetMovies()

all = []

if 'result' in retrieved and 'movies' in retrieved['result']:
  for v in retrieved['result']['movies']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('MOVIES', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate SHOWS Slot
retrieved = kodi.GetTvShows()

all = []

if 'result' in retrieved and 'tvshows' in retrieved['result']:
  for v in retrieved['result']['tvshows']:
    name = kodi.sanitize_name(v['label'], normalize=False)
    name_stripped = kodi.sanitize_name(v['label'], True, False)
    all.append(name)
    all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('SHOWS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()


# Generate ADDONS Slot
all = []

for content in ['video', 'audio', 'image', 'executable']:
  retrieved = kodi.GetAddons(content)

  if 'result' in retrieved and 'addons' in retrieved['result']:
    for v in retrieved['result']['addons']:
      name = kodi.sanitize_name(v['name'], normalize=False)
      name_stripped = kodi.sanitize_name(v['name'], True, False)
      all.append(name)
      all.append(name_stripped)

cleaned = list(set(all))
cleaned = filter(None, cleaned)
random.shuffle(cleaned)
cleaned = cleaned[:100]

gfile = open('ADDONS', 'w')
for a in cleaned:
  gfile.write("%s\n" % a.encode("utf-8"))
gfile.close()
