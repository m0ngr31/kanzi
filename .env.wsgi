# The Kodi webserver only supports HTTP.
# Uncomment KODI_SCHEME to tell the skill to use https between AWS/Heroku and your local network
# (only use if you have already set this up with your own certificates)
#
# KODI_SCHEME=https

# If using a reverse proxy you might need to add an extra bit to the url before "jsonrpc"
# You can do this with KODI_SUBPATH (don't use slashes before or after)
#
# KODI_SUBPATH=

KODI_ADDRESS=
KODI_PORT=
KODI_USERNAME=
KODI_PASSWORD=
SKILL_APPID=
SKILL_VERIFY_CERT=
BROADCAST_LOAD_TIMEOUT=
BROADCAST_SCAN_TIMEOUT=
