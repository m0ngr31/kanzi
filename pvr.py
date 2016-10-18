#!/usr/bin/env python

import kodi
import re
import sys
from pvr_channel_alias import PVR_CHANNEL_ALIAS
from pvr_search_channels import PVR_SEARCH_CHANNELS

PVR_CHANNELS_BY_LABEL = {}
PVR_CHANNELS_BY_ID = {}
PVR_BROADCASTS = {}


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


def get_pvr_channels_by_label():
    global PVR_CHANNELS_BY_LABEL
    if PVR_CHANNELS_BY_LABEL:
        print('Using pre-loaded list of PVR channels')
        sys.stdout.flush()
    else:
        print('Loading list of PVR channels...')
        sys.stdout.flush()

        pvr_channels_response = kodi.GetPVRChannels()
        if 'result' in pvr_channels_response and 'channels' in pvr_channels_response['result']:
            for channel in pvr_channels_response['result']['channels']:
                channel_label = channel['label']
                PVR_CHANNELS_BY_LABEL[word_to_number(channel_label).lower()] = channel['channelid']
                try:
                    # add alias channels as 'real' channels for easy of lookup
                    pvr_channel_alias = PVR_CHANNEL_ALIAS[channel_label]
                    PVR_CHANNELS_BY_LABEL[word_to_number(pvr_channel_alias).lower()] = channel
                    print('added alias for %s' % (channel_label))
                except:
                    pass

        else:
            raise IOError('Error parsing results.')
    return PVR_CHANNELS_BY_LABEL


def get_pvr_channels_by_id():
    global PVR_CHANNELS_BY_ID
    if PVR_CHANNELS_BY_ID:
        print('Using pre-loaded list of PVR channels')
        sys.stdout.flush()
    else:
        print('Loading list of PVR channels...')
        sys.stdout.flush()

        pvr_channels_response = kodi.GetPVRChannels()
        if 'result' in pvr_channels_response and 'channels' in pvr_channels_response['result']:
            PVR_CHANNELS_BY_ID = {channel['channelid']: word_to_number(channel['label']).lower() for channel in pvr_channels_response['result']['channels']}
        else:
            raise IOError('Error parsing results.')
    return PVR_CHANNELS_BY_ID


def get_pvr_broadcasts():
    global PVR_BROADCASTS
    if PVR_BROADCASTS:
        print('Using pre-loaded broadcasts data')
        sys.stdout.flush()
    else:
        print('Loading broadcasts data...')
        sys.stdout.flush()

        PVR_BROADCASTS = {}
        for id, channel in get_pvr_channels_by_id().iteritems():
            try:
                PVR_SEARCH_CHANNELS.index(channel)
                pvr_broadcasts_response = kodi.GetPVRBroadcasts(id)

                if 'result' in pvr_broadcasts_response:
                    if 'broadcasts' in pvr_broadcasts_response['result']:
                        pvr_broadcasts = pvr_broadcasts_response['result']['broadcasts']
                        PVR_BROADCASTS[id] = pvr_broadcasts
                        print('Added broadcasts for %s' % (channel))
                else:
                    raise IOError('Error parsing broadcast results.')
            except ValueError:
                pass
    return PVR_BROADCASTS