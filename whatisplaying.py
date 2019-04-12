import re
import string
import random
import os
import time
from kodi_voice import KodiConfigParser, Kodi

config_file = os.path.join(os.path.dirname(__file__), "kodi.config")
config = KodiConfigParser(config_file)

kodi = Kodi(config)

print kodi.GetActivePlayItem(),"\n"
print kodi.GetActivePlayProperties(),"\n"
#time.sleep(5)

