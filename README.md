# Alexa integration with Kodi

I'm forking this code off of [this project from Maker Musings](http://www.makermusings.com/2015/08/22/home-automation-with-amazon-echo-apps-part-2). It originally supported checking to see how many new episodes there are and you can ask it if there are any new episodes for a certain show.

I've expanded it to support the following features:
  - Basic navigation (Up/Down, Left/Right, Page Up/Down, Select, Back, Open Menu) 
  - Playback control (Play/Pause, Skip, Previous, Stop)
  - Shuffle music by artist
  - Play random episode of TV show
  - Play random movie
  - Play specific episode of a TV show ('Play season 4 episode 10 of The Office')
  - Play specific movie

### Setup

To get this running, you'll have to have your own server to handle the requests and pass them to your Kodi box. I've found the easiest way to get something up and running is to use [OpenShift](https://openshift.redhat.com/).

OpenShift makes it easy to get it up and running and it is completely free to use. This way you won't have to worry about spinning up a VPS somewhere and fiddling with SSL certs, WSGI configs, Python packages, ect. Heroku will work fine as well, and has a similar setup, but the free tier requires the `dyno` to sleep for 6 hours a day and goes to sleep after approximately 30 minutes of inactivity, which would be a hassle to deal with.

Once you have setup an OpenShift account setup, go ahead and [install the command line tool](https://developers.openshift.com/en/managing-client-tools.html) (You'll need Ruby installed). From the cli, you'll be able to create a new app that will create a folder with a git repo initialized. Go into that directory and replace the `wsgi.py` file and add the `kodi.py` and `requirements.txt` files from this repo.

Once you have everything ready, you can setup the following environment variables to talk to your Kodi box:

  - KODI_ADDRESS
  - KODI_PORT
  - KODI_USERNAME
  - KODI_PASSWORD

If you would rather not set this up, you can change the values in the `kodi.py` file. Just remember that this transmits your Kodi username and password in plaintext over HTTP, so make sure it's not something that you are using for other accounts.

Of course you'll need to have your Kodi box opened up to the internet via port forwarding. If you don't have a dedicated IP address, you'll also need a dynamic DNS service to give you a static URL to use so you don't have to be constantly change this value.

Once you have this all setup, you'll need to setup an Amazon developer account and start setting up a new Alexa skill.

Here's what it'll look like:
![1st tab](http://i.imgur.com/q0Wqld1.png)
You'll just need to stick the URL from your app in the Endpoint field

On the next tab, you'll have to paste the `alexa.intents` file into the first field, and use [this tool here](http://www.makermusings.com/amazon-echo-utterance-expander/) to create the Sample utterances from the `alexa.utterances` file in the second field.
![2nd tab](http://i.imgur.com/UcXVqSO.png)

The next tab has info about the SSL cert, if you are using OpenShift, select the middle option.
![3rd tab](http://i.imgur.com/moGJQrx.png)

After that is pretty much just information that you can just put whatever into. Don't submit it for certification since only you will be using your server.

### Performing voice commands

Here are a few demo videos showing how to use it. Other commands you can do are in the utterances file.

[![Amazon Echo - Kodi integration (demo 1) ](http://img.youtube.com/vi/Xar4byrlEvo/0.jpg)](https://www.youtube.com/watch?v=Xar4byrlEvo "Amazon Echo - Kodi integration (demo 1) ")

[![Amazon Echo - Kodi integration (demo 2) ](http://img.youtube.com/vi/vAYUWaP3EXA/0.jpg)](https://www.youtube.com/watch?v=vAYUWaP3EXA "Amazon Echo - Kodi integration (demo 2) ")

[![Amazon Echo - Kodi integration (demo 3) ](http://img.youtube.com/vi/4xrrEkimPV4/0.jpg)](https://www.youtube.com/watch?v=4xrrEkimPV4 "Amazon Echo - Kodi integration (demo 3) ")
