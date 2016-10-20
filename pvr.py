#!/usr/bin/env python

import os
import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import kodi
import re
import sys
import threading
from pvr_channel_alias import PVR_CHANNEL_ALIAS
from collections import OrderedDict

BROADCAST_LOAD_TIMEOUT = int(os.getenv('BROADCAST_LOAD_TIMEOUT', '15'))
BROADCAST_SCAN_TIMEOUT = int(os.getenv('BROADCAST_SCAN_TIMEOUT', '15'))

PVR_CHANNELS_BY_LABEL = OrderedDict()
PVR_BROADCASTS = OrderedDict()
PVR_FAVOURITE_BROADCASTS = {}


def word_to_number(input):
  input = re.sub(r'1', ' 1 ', input, flags=re.IGNORECASE)
  input = re.sub(r'2', ' 2 ', input, flags=re.IGNORECASE)
  input = re.sub(r'3', ' 3 ', input, flags=re.IGNORECASE)
  input = re.sub(r'4', ' 4 ', input, flags=re.IGNORECASE)
  input = re.sub(r'5', ' 5 ', input, flags=re.IGNORECASE)
  input = re.sub(r'6', ' 6 ', input, flags=re.IGNORECASE)
  input = re.sub(r'7', ' 7 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bone\b', ' 1 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\btwo\b', ' 2 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bthree\b', ' 3 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bfour\b', ' 4 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bfive\b', ' 5 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bsix\b', ' 6 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\bseven\b', ' 7 ', input, flags=re.IGNORECASE)
  input = re.sub(r'\ \ ', ' ', input, flags=re.IGNORECASE)
  input = re.sub(r'\ \+', ' plus', input, flags=re.IGNORECASE)
  input = re.sub(r'\+', ' plus', input, flags=re.IGNORECASE)
  return input.strip()


def get_pvr_channels_by_label(force_load = True):
    global PVR_CHANNELS_BY_LABEL
    if PVR_CHANNELS_BY_LABEL and not force_load:
        print('Using pre-loaded list of PVR channels')
        sys.stdout.flush()
    else:
        print('Loading list of PVR channels...')
        sys.stdout.flush()

        pvr_channels_by_label = {}
        pvr_channels_response = kodi.GetPVRChannels()
        if 'result' in pvr_channels_response and 'channels' in pvr_channels_response['result']:
            for channel in pvr_channels_response['result']['channels']:
                channel_label = channel['label']
                pvr_channels_by_label[word_to_number(channel_label).lower()] = channel['channelid']
                try:
                    # add alias channels as 'real' channels for easy of lookup
                    pvr_channel_alias = PVR_CHANNEL_ALIAS[channel_label]
                    pvr_channels_by_label[word_to_number(pvr_channel_alias).lower()] = channel['channelid']
                    print('added alias for %s' % (channel_label))
                except:
                    pass

        else:
            raise IOError('Error parsing results.')

        PVR_CHANNELS_BY_LABEL = pvr_channels_by_label

        # reload the channels list in around 2 hours time
        c = threading.Timer(7000.0, get_pvr_channels_by_label, [True])
        c.daemon = True
        c.start()
    return PVR_CHANNELS_BY_LABEL


def get_pvr_broadcasts(force_load = False, timeout_seconds = BROADCAST_LOAD_TIMEOUT):
    global PVR_BROADCASTS
    if PVR_BROADCASTS and not force_load:
        print('Using pre-loaded broadcasts data')
        sys.stdout.flush()
    else:
        print('Loading broadcasts data...')
        sys.stdout.flush()

        pvr_broadcasts = {}
        stop_time = datetime.datetime.utcnow() + datetime.timedelta(0, timeout_seconds)
        for channel, id in get_pvr_channels_by_label().iteritems():
            if datetime.datetime.utcnow() > stop_time:
                print('timed out after %s seconds' % (timeout_seconds))
                break

            pvr_broadcasts_response = kodi.GetPVRBroadcasts(id)

            if 'result' in pvr_broadcasts_response:
                if 'broadcasts' in pvr_broadcasts_response['result']:
                    pvr_broadcasts[id] = pvr_broadcasts_response['result']['broadcasts']
                    print('Added broadcasts for %s' % (channel))
            else:
                raise IOError('Error parsing broadcast results.')

        PVR_BROADCASTS = pvr_broadcasts

        # reload the broadcasts in a hour
        c = threading.Timer(3600.0, get_pvr_broadcasts, [True, 60])
        c.daemon = True
        c.start()
    return PVR_BROADCASTS
