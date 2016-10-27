#!/bin/python

# By default lambda-deploy will package the entire folder it is run from and
# upload it to AWS. To keep things a little neater you can run this script to
# copy the Lambda relevant files to a seperate folder then deploy from the new 
# folder.
# 
# Usage: `python deploy-to-lambda.py`

import subprocess
import os
import shutil

app_name = "kodi-alexa"

if(os.path.isdir(app_name)):
  shutil.rmtree(app_name, ignore_errors=True)

os.mkdir(app_name)

if(os.path.isfile(".env")):
  shutil.copy(".env", app_name)

if(os.path.isfile("kodi.py")):
  shutil.copy("kodi.py", app_name)

if(os.path.isfile("wsgi.py")):
  shutil.copy("wsgi.py", app_name)

if(os.path.isfile("requirements.txt")):
  shutil.copy("requirements.txt", app_name)

os.chdir(app_name)
print subprocess.Popen("lambda-deploy deploy", shell=True, stdout=subprocess.PIPE).stdout.read()  