import kodi
import re
import string

# to use put the Kodi details into environment variables
# KODI_ADDRESS=localhost KODI_PORT=8088 KODI_USERNAME=kodi KODI_PASSWORD=kodi python generate_custom_types.py

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


# Generetate SHOWS Slot
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
