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

# Your local time zone for responses that include absolute times.
# See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
#
# For example, if you are in the Eastern US time zone, you would use:
# SKILL_TZ=US/Eastern
#
# Leave empty or undefined (commented out) if you don't need or want absolute
# time responses.  An example is asking when the currently playing item will
# end.  If you have SKILL_TZ defined, it will also tell you the wall-clock
# time when the item will conclude.
SKILL_TZ=

# Requests post timeout in seconds.
#
# It's the time alexa waits for a response from Kodi before giving up.
# It is an helpful value, especially if not run as lambda, since the Web Service might
# hang indefinitely waiting for a response.
KODI_RPC_TIMEOUT = 60
