import kodi
import re
import string
from yaep import populate_env

# to use put the Kodi details into environment variables
# KODI_ADDRESS=localhost KODI_PORT=8088 KODI_USERNAME=kodi KODI_PASSWORD=kodi python generate_custom_types.py
populate_env()

# Generate MUSICARTISTS Slot
retrieved = kodi.GetMusicArtists()

all = []

if 'result' in retrieved and 'artists' in retrieved['result']:
  for v in retrieved['result']['artists']:
    ascii_name = v['artist'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MUSICARTISTS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate MUSICALBUMS Slot
retrieved = kodi.GetAlbums()

all = []

if 'result' in retrieved and 'albums' in retrieved['result']:
  for v in retrieved['result']['albums']:
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MUSICALBUMS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate MUSICSONGS Slot
retrieved = kodi.GetSongs()

all = []

if 'result' in retrieved and 'songs' in retrieved['result']:
  for v in retrieved['result']['songs']:
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MUSICSONGS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate MUSICPLAYLISTS Slot
retrieved = kodi.GetMusicPlaylists()

all = []

if 'result' in retrieved and 'files' in retrieved['result']:
  for v in retrieved['result']['files']:
    # Strip characters and parentheses
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MUSICPLAYLISTS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate VIDEOPLAYLISTS Slot
retrieved = kodi.GetVideoPlaylists()

all = []

if 'result' in retrieved and 'files' in retrieved['result']:
  for v in retrieved['result']['files']:
    # Strip characters and parentheses
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('VIDEOPLAYLISTS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate MOVIEGENRES Slot
retrieved = kodi.GetMovieGenres()

all = []

if 'result' in retrieved and 'genres' in retrieved['result']:
  for v in retrieved['result']['genres']:
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MOVIEGENRES', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate MOVIES Slot
retrieved = kodi.GetMovies()

all = []

if 'result' in retrieved and 'movies' in retrieved['result']:
  for v in retrieved['result']['movies']:
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MOVIES', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate SHOWS Slot
retrieved = kodi.GetTvShows()

all = []

if 'result' in retrieved and 'tvshows' in retrieved['result']:
  for v in retrieved['result']['tvshows']:
    ascii_name = v['label'].encode('ascii', 'replace')
    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
    all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('SHOWS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()


# Generate ADDONS Slot
all = []

for content in ['video', 'audio', 'image', 'executable']:
  retrieved = kodi.GetAddons(content)

  if 'result' in retrieved and 'addons' in retrieved['result']:
    for v in retrieved['result']['addons']:
      ascii_name = v['name'].encode('ascii', 'replace')
      removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
      all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('ADDONS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()

# Generetate CHANNELS Slot
retrieved = kodi.GetPVRChannels()

all = []

if 'result' in retrieved and 'channels' in retrieved['result']:
  for v in retrieved['result']['channels']:
    ascii_name = v['label'].encode('ascii', 'replace')
#    removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
#    all.append(removed_paren.encode('utf-8').strip())
    all.append(ascii_name.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('CHANNELS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()

# Generetate BROADCASTS Slot
retrieved = kodi.GetPVRChannels()

all = []

if 'result' in retrieved and 'channels' in retrieved['result']:
  for v in retrieved['result']['channels']:
    channelid = v['channelid']
    broadcasts = kodi.GetPVRBroadcasts(channelid)
    if 'result' in broadcasts and 'broadcasts' in broadcasts['result']:
      for broadcast in broadcasts['result']['broadcasts']:
        ascii_name = broadcast['label'].encode('ascii', 'replace')
        removed_paren = re.sub(r'\([^)]*\)', '', ascii_name).rstrip().lower().translate(None, string.punctuation)
        all.append(removed_paren.encode('utf-8').strip())

deduped = list(set(all))

gfile = open('BROADCASTS', 'w')
for a in deduped:
  gfile.write("%s\n" % a)
gfile.close()
