import kodi

# to use put the Kodi details into environment variables
# KODI_ADDRESS=localhost KODI_PORT=8088 KODI_USERNAME=kodi KODI_PASSWORD=kodi python generate_custom_types.py

retrieved = kodi.GetMusicArtists()
print retrieved
all = []
for v in retrieved['result']['artists']:
    all.append(v['artist'].encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MUSIC', 'w')
for a in deduped:
    gfile.write("%s\n" % a)
gfile.close()

retrieved = kodi.GetMovies()

all = []
for v in retrieved['result']['movies']:
    all.append(v['label'].encode('utf-8').strip())

deduped = list(set(all))

gfile = open('MOVIES', 'w')
for a in deduped:
    gfile.write("%s\n" % a)
gfile.close()


retrieved = kodi.GetTvShows()

all = []
for v in retrieved['result']['tvshows']:
    all.append(v['label'].encode('utf-8').strip())

deduped = list(set(all))

gfile = open('SHOW', 'w')
for a in deduped:
    gfile.write("%s\n" % a)
gfile.close()

