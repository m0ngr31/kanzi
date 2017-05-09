#!/usr/bin/env python

import os
import requests
import json
from urlparse import urlparse
import subprocess

res = requests.get('http://localhost:4040/api/tunnels')
assert res.status_code == 200
content = res.json()
tunnels = content['tunnels']
assert len(tunnels) == 2 # http, https
public_url = tunnels[0]['public_url']
domain = urlparse(public_url).netloc
env_content = open('.env_no_url', 'rb').read()
assert '{KODI_ADDRESS}' in env_content
assert '{KODI_USERNAME}' in env_content
assert '{KODI_PASSWORD}' in env_content
assert '{AWS_ACCESS_KEY_ID}' in env_content
assert '{AWS_SECRET_ACCESS_KEY}' in env_content
assert '{LAMBDA_ROLE}' in env_content
env_content = env_content.replace('{KODI_ADDRESS}', domain)
env_content = env_content.replace('{KODI_USERNAME}', os.environ['KODI_USERNAME'])
env_content = env_content.replace('{KODI_PASSWORD}', os.environ['KODI_PASSWORD'])
env_content = env_content.replace('{AWS_ACCESS_KEY_ID}', os.environ['AWS_ACCESS_KEY_ID'])
env_content = env_content.replace('{AWS_SECRET_ACCESS_KEY}', os.environ['AWS_SECRET_ACCESS_KEY'])
env_content = env_content.replace('{LAMBDA_ROLE}', os.environ['LAMBDA_ROLE'])
open('.env', 'wb').write(env_content)

print 'Deploying'
print subprocess.Popen("lambda-deploy deploy", shell=True, stdout=subprocess.PIPE).stdout.read()  
