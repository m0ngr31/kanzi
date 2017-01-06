import os
import collections

def has_music_functionality():
  try:
    import pymongo
  except:
    return False

  accepted_answers = ['y', 'yes', 'Y', 'Yes', 'YES', 'true', 'True']
  accepted_warning = os.getenv('ACCEPT_MUSIC_WARNING')

  if accepted_warning in accepted_answers:
    if os.getenv('MONGODB_USER') and os.getenv('MONGODB_PASS') and os.getenv('MONGODB_URL') and os.getenv('MONGODB_PORT') and os.getenv('MONGODB_NAME'):
      return True
    else:
      return False
  else:
    return False

class MusicPlayer:
  def __init__(self, urls=[]):
    from pymongo import MongoClient
    self.mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (os.getenv('MONGODB_USER'), os.getenv('MONGODB_PASS'), os.getenv('MONGODB_URL'), int(os.getenv('MONGODB_PORT')), os.getenv('MONGODB_NAME'))
    self.client = MongoClient(self.mongo_uri)
    self.db = self.client[os.getenv('MONGODB_NAME')]
    self.playlists = self.db['playlist-info']

    if len(urls) > 0:
      self.clean_init(urls)
    else:
      self.load_from_mongo()

  @property
  def next_item(self):
    if self.current_index < (len(self.urls) - 1):
      return self.urls[self.current_index + 1]
    else:
      return None

  @property
  def prev_item(self):
    if self.current_index > 0:
      return self.urls[self.current_index - 1]
    else:
      return None

  def skip_song(self):
    self.current_offset = 0
    self.current_index += 1
    self.current_item = self.urls[self.current_index]

    self.save_to_mongo()

  def prev_song(self):
    self.current_offset = 0
    self.current_index -= 1
    self.current_item = self.urls[self.current_index]

    self.save_to_mongo()

  def clean_init(self, urls):
    self.urls = urls
    self.current_item = urls[0]
    self.current_index = 0
    self.current_offset = 0

    self.save_to_mongo()

  def load_from_mongo(self):
    playlist_data = self.playlists.find_one()
    self.urls = playlist_data['urls']
    self.current_item = playlist_data['current_item']
    self.current_index = playlist_data['current_index']
    self.current_offset = playlist_data['current_offset']

  def save_to_mongo(self):
    self.playlists.drop()

    playlist_data = {
      "urls": self.urls,
      "current_item": self.current_item,
      "current_index": self.current_index,
      "current_offset": self.current_offset
    }

    self.playlists.insert_one(playlist_data)
