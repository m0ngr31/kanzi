# Alexa integration with Kodi

## Updating

If you are updating from a previous version, **it is very important that you browse to the UPGRADING.md file and look at what you need to do.**

## About

Here are some of the features supported by this skill:

- Basic navigation (Up/Down, Left/Right, Page Up/Down, Select, Back, Menu, Zoom, Rotate, Move)
- Open library views (Movies, Shows, Music, Artists, Albums, Music Videos, Playlists)
- Open library views by genre (Movies, Shows, Music, Music Videos)
- Open recently added playlists (Movies, Episodes, Albums, Music Videos)
- Playback control (Play/Pause, Skip, Previous, Stop, Step/Jump)
- Adjust volume
- Shuffle all music by an artist
- Play/Shuffle specific album
- Play/Shuffle the latest album by an artist
- Play a specific song
- Play/Shuffle audio and video playlists
- "Party mode" for music (shuffle all)
- Play/Shuffle music videos
- Play/Shuffle music videos from a specific genre
- Play/Shuffle music videos by a specific artist
- Shuffle all episodes of a TV show
- Play random TV show
- Play random TV show from a specific genre
- Play random episode of a specific TV show
- Play specific episode of a TV show ('Play season 4 episode 10 of The Office')
- Play random movie
- Play random movie from a specific genre
- Play specific movie
- Play trailer for a movie in your library (*requires plugin.video.youtube addon*)
- Play random music video
- Play random music video from a specific genre
- Continue watching next episode of last show that was watched
- Play next episode of a show
- Play newest episode of a show
- Recommend media to watch/listen to
- List/Play recently added media
- List available albums by an artist
- Clean/Update video and audio sources
- "What's playing?" functionality for music, movies, and shows
- Report time remaining on current media and when it will end
- Cycle through audio and subtitle streams
- Search for something in your library (*requires script.globalsearch addon*)
- Execute addons
- Shutdown/reboot/sleep/hibernate system
- Toggle fullscreen
- Eject media

## Initial Computer Setup
Unless you are going to host the skill on Heroku, there are a few things in the instructions that you will need to install before you can get started: 

 - **Python 2.7 (Python 3 will not work)**
 - Git

 There are numerous tutorials online about how to install these, so just Google how to install them on your OS if you are uncertain about how to proceed.

## Kodi Setup

Before a command from Alexa can be sent to your [Kodi](https://kodi.tv) box, you need to enable the "Allow remote control via HTTP", "Allow remote control from applications on this system", and "Allow remote control from applications on other systems" options in your [Kodi](https://kodi.tv) settings. Note that wording might be change a little bit on different versions, this example is for [Kodi](https://kodi.tv) 17.

![Kodi settings](http://i.imgur.com/YMqS8Qj.png)

Make sure to keep track of the port, username, and password you are using.

Now, you'll need to have your [Kodi](https://kodi.tv) box opened up to the internet via port forwarding.

If you don't have a dedicated IP address, you'll need a dynamic DNS service to give you a static URL to use so you don't have to be constantly change this value.

Repeat the above for each instance of [Kodi](https://kodi.tv) that you wish to control via the skill.  Remember you will need to open a separate, unique port on your router for each instance of [Kodi](https://kodi.tv).

Once you get that setup, you'll have to have your own server to handle the requests and pass them to your [Kodi](https://kodi.tv) box. Since this is a Python application, it has several ways that you can run it. Here are a few options to get started:

- [Heroku](#heroku)
- [AWS Lambda](#aws-lambda)
- [Docker](#docker)

If you plan on running your own Apache/Nginx server, I'm sure you can figure that out yourself. Skip ahead to the [Skill setup section](#skill-setup). Keep in mind that you will have to generate a self-signed SSL cert (or Let's Encrypt) so that Amazon will allow you to use it.

### Note regarding MySQL and performance

If you are using [MySQL](https://www.mysql.com) as a database backend for [Kodi](https://kodi.tv), please note that there are known issues with the optimizer in [MySQL](https://www.mysql.com) 5.7.6+ that will cause any commands that involve queueing items in bulk to be tremendously slow.  There is nothing in the skill we can do to fix this, as it is technically a [MySQL](https://www.mysql.com) bug/limitation; however, you can either stay on [MySQL](https://www.mysql.com) < 5.7.6 or you can easily migrate to another that doesn't have this problem, such as [MariaDB](https://mariadb.org).

As far as we are aware, [SQLite](https://sqlite.org) and [Emby](https://emby.media) do not share this issue.

## Heroku
### Pricing
[Heroku](https://heroku.com/) is a great way to get a server running for free, but there is a small limitation with the free tier on Heroku where the 'dyno' will go to sleep after 30 minutes of in-activity. This might cause some commands to timeout, but so far it seems to be the best option for getting up and running as quickly as possibly. To get around this, you can either pay for a "Hobby" server which is only $7/month. If you really don't want to pay, there is a work-a-round where you get enough free hours a month to leave this server running 24/7 if you add your Credit Card to your account. Then you can use something like [Kaffeine](http://kaffeine.herokuapp.com/) to keep it from spinning down.

### Limitations
Currently we do not support addressing multiple instances of [Kodi](https://kodi.tv) with [Heroku](https://heroku.com/).  If you wish to control multiple instances of [Kodi](https://kodi.tv), you will need to set up multiple copies of the skill to do so.

### Setup
After you've setup an Heroku account, click on this button below to provision a new server. Select a unique name to make upgrades easy.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy/?template=https://github.com/m0ngr31/kodi-alexa)

Now skip ahead to the [Skill setup section](#skill-setup).

## AWS Lambda
### Pricing
Lambda is a great service which lets the skill run "serverless". AWS provides credits for new accounts and should allow you to run everything the skill needs for free for 12 months. Once you are being billed for it, it will be less than $0.20/month. Very reasonable for what it offers.

### Setup
Getting going on Lambda is pretty straightforward. First, you'll need to create an Amazon developer account if you don't have one already. After that, browse to the [IAM Management Console](https://console.aws.amazon.com/iam/home) where you will create a new user:

![First page](http://i.imgur.com/rymHquZ.png)
You can enter whatever username you want here, but make sure that Programmatic access is checked.

![Second page](http://i.imgur.com/TXX25BI.png)
Attach the 'AdministratorAccess` permission to the new user.

![Third page](http://i.imgur.com/83o9cen.png)
Confirmation page should look like this.

![Fourth page](http://i.imgur.com/3PZM92w.png)
Once you get here, do not leave the page! You need the Access key ID and Secret access key for the next step. If you close now you'll have to create a new user. You can't get access to the Secret access key again.

Next, run these commands to configure your computer for AWS service access:
`pip install awscli` and then `aws configure`. Just follow the prompts, and copy paste the keys when it asks for them. When it asks for location, if you are in the US, enter: `us-east-1`, and if you are in Europe: `eu-west-1`.

After you've done that, run `pip install virtualenv`. This is required for a later step.

Now, clone my repo: `git clone https://github.com/m0ngr31/kodi-alexa.git` and `cd kodi-alexa`. Once you are inside the project directory, you're going to create a new "Virtual environement" and then activate it:
`virtualenv venv` and `source venv/bin/activate` (if you are on Windows, that's `venv\Scripts\activate.bat` or `venv\Scripts\activate.ps1` for Powershell).

After successful completion, run `pip install -r requirements.txt`, `pip install packaging`, and `pip install zappa`.

Before you deploy, you need to create the file `kodi.config` from the [kodi.config.example template](https://raw.githubusercontent.com/m0ngr31/kodi-voice/master/kodi_voice/kodi.config.example) and enter the correct information for: address, port, username, and password. I'll go over the other variables in another section below.

Before you can send any code to Lambda, you'll need to set up Zappa. Just run `zappa init` and accept the defaults for everything. If it doesn't automatically detect that this is a Flask app, tell it that the application function is `alexa.app`.

To make an initial deployment to Lambda, just run the following command: `zappa deploy dev`. It'll take a few minutes, and at the end it will give you a URL that you will need to copy. It will look like this:
![Lambda deploy](http://i.imgur.com/5rtN5ls.png)

You are now running on Lambda! To update after there is a change here, or you updated your env variables, see the instructions in UPGRADING.md.

Now skip ahead to the [Skill setup section](#skill-setup).

## Docker

### 1. Manually creating the docker image

```bash
docker build -t kodi-alexa .
```

### 2. Running docker image using env variables
```bash
docker run --name=kodi-alexa -d --restart always -v ~/kodi-alexa-config:/config -p 8000:8000 -e "KODI_ADDRESS=192.168.54.14" -e "SKILL_APPID=xxx" -e "KODI_PORT=8080" kodi-alexa
```
where 
 - KODI_ADDRESS is the ip address of the kodi media player
 - KODI_PORT is the port the Kodi api is listening on

 If you would like docker-compose yaml to create the container:
```yaml
   kodi-alexa:
    container_name: kodi-alexa
    image: kodi-alexa
    network_mode: bridge
    restart: always
    ports:
      - 8000:8000/tcp
    environment:
      - KODI_ADDRESS=192.168.54.127
      - KODI_PORT=8080
      - SKILL_APPID="XXXX"
      - MAX_UNWATCHED_SHOWS=15
      - MAX_UNWATCHED_EPISODES=15
      - MAX_UNWATCHED_MOVIES=15
    hostname: kodi-alexa
    volumes:
      - ~/kodi-alexa-config:/config
```

 The image autocreates a self signed certificate, so there is no need for you to do anything about that. If you have a valid cetficate just replace the one in the ~/kodi-alexa-config.
 Any Heroku env variable is also available to add when creating the docker container.
 If you want the more advanced setup, with kodi.config, just place that file inside ~/kodi-alexa-config directory and restart the container.

 ### 3. Exporting kodi-alexa on the internet so the skill can access it.
  - basically you will need to map port 443 on your router to your docker server, port 8000, as described. This way the amazon skill can access it directly, and in turn kodi-alexa can then issue a command to you local kodi instance/instances. There is a lot of info on how to do this, just google "port forward *your router model*". You can also get some info here: https://www.howtogeek.com/66214/how-to-forward-ports-on-your-router/
  - If your IP address changes, then you will most likely need to setup a Dynamic DNS name. More info [here](https://en.wikipedia.org/wiki/Dynamic_DNS). I recommend [noip](https://www.noip.com/free) but any other free DDNS provider should do the job.



# Skill Setup

If you are self-hosting, you will need to create the file `kodi.config` from the [kodi.config.example template](https://raw.githubusercontent.com/m0ngr31/kodi-voice/master/kodi_voice/kodi.config.example).  The template file contains comments to describe the options.

Once you've set up your server, you'll need to configure a new Alexa skill. Head over to the [Skills list on Amazon's developer page](https://developer.amazon.com/edw/home.html#/skills/list) and hit the 'Add new skill' button.

The initial setup page looks like this:
![Inital setup skill](http://i.imgur.com/AzufQxo.png)

On the next page, you'll have to paste the contents of the [IntentSchema.json](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/IntentSchema.json) file into the "Intent Schema" field, and paste the contents of the [SampleUtterances.en.txt](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/SampleUtterances.en.txt) or [SampleUtterances.de.txt](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/SampleUtterances.de.txt) file in the "Sample Utterances" field. **Generate and save your Custom Slots first before pasting the Intents and Utterances to avoid errors when attempting to save**.

You need to create the following slots:
- MOVIES
- MOVIEGENRES
- SHOWS
- SHOWGENRES
- MUSICVIDEOS
- MUSICVIDEOGENRES
- MUSICARTISTS
- MUSICALBUMS
- MUSICSONGS
- MUSICGENRES
- MUSICPLAYLISTS
- VIDEOPLAYLISTS
- ADDONS

To make it as easy as possible, I wrote a little webapp that will give you the information you need: [here](https://slot-generator.herokuapp.com/).

You can also get the information from running `python generate_custom_slots.py` in the project directory. This will create txt files with the relevant information. This will communicate with the Kodi instance defined in the `[DEFAULT]` section in `kodi.config`. *NOTE: If you're deploying to Heroku, you cannot use the python slot generator unless you create the kodi.config file.  It's best to use the webapp for generating slots in this case.*

If one of your slots is empty, you can just enter the word 'Empty' or something so that it'll save.

![2nd tab](http://i.imgur.com/WQYExdK.png)

The next tab has info about the server. Enter your Heroku, Lambda, or self-hosted URL here.
![3rd tab](http://i.imgur.com/GjFvKYv.png)

The fourth tab is asking about the SSL certificate. If you are using Heroku, Lambda or Docker, select the middle option.

![3rd tab](http://i.imgur.com/moGJQrx.png)

After that is pretty much just information that you can just put whatever into. Don't submit it for certification since only you will be using your server.

And now you should be set! Go ahead and try speaking a few commands to it and see if it works! If you can't get it working, see the [Getting Help section](#getting-help).

Thanks!

# Controlling more than one instance of Kodi

As of version 2.6 of the skill, it can now control more than one instance of [Kodi](https://kodi.tv).  The skill determines which instance to talk to by determining which Echo device received the command.

You set up the mapping in the `kodi.config` file.  There are a few examples there with dummy device IDs.

If a device ID isn't explicitly present in the config file, it will utilize the details in the `[DEFAULT]` section.  So, for example, if you wanted most of your devices to send commands to [Kodi](https://kodi.tv) in your living room, you would set the `[DEFAULT]` section to point at that instance.  For any that you want to override -- say, office and master bedroom -- you would define override sections with those device IDs.

Further, for override sections, if a variable isn't defined, it will inherit it from the `[DEFAULT]` section.  Thus, if the only thing you need to change is `address` and `port`, define just those in the override.  You do not need to copy all of the other variables as well.

## Getting the device IDs

When you send a request to the skill, it will log an entry on the skill's server that will look something like this:

`Sending request to http://mydomain.com:8080/jsonrpc from device amzn1.ask.device.AEFDXCGLSFJFNGCVF8SDJF90FID9G284JDJFGJGHH83358DJFFGIGD734JJDFGK211GDFFHHH23HGFJTYEFGJRT56KJDHDFJ5546DJDFFSWOPPP677P88P873EHZNZDFEIRTYIN2239NDFGIH724JDFKS2AA`

For AWS Lambda/Zappa deployments, you can access your logs with:

`zappa tail dev`

To generate your override sections, you will want to tail (watch the end of) the log file and send any request (like, `Alexa, ask Kodi what is playing?`) from the Echo device you wish to override.  Look for a line that looks like the above.  The device ID is everything from `amzn1.ask.device.` to the end of the line.  Copy this text and paste it to the end of the `kodi.config` file, placing it within square brackets `[]`, like so:

`[amzn1.ask.device.AEFDXCGLSFJFNGCVF8SDJF90FID9G284JDJFGJGHH83358DJFFGIGD734JJDFGK211GDFFHHH23HGFJTYEFGJRT56KJDHDFJ5546DJDFFSWOPPP677P88P873EHZNZDFEIRTYIN2239NDFGIH724JDFKS2AA]`

Anything in square brackets denotes a new section.  In this section, you can override whatever variables you'd like.  In this example, this Echo device is my Echo Dot in the office, so I would do something like:

```
# Office Echo Dot
[amzn1.ask.device.AEFDXCGLSFJFNGCVF8SDJF90FID9G284JDJFGJGHH83358DJFFGIGD734JJDFGK211GDFFHHH23HGFJTYEFGJRT56KJDHDFJ5546DJDFFSWOPPP677P88P873EHZNZDFEIRTYIN2239NDFGIH724JDFKS2AA]
address = office-dot
```

# Additional validation of requests

To verify that incoming requests are only allowed from your own copy of the skill, you can set the `skill_id` configuration variable to your own Application ID; e.g., `amzn1.ask.skill.deadbeef-4e4f-ad61-fe42-aee7d2de083d`

# Extra settings for more functionality

Setting the `timezone` configuration variable will make it so when you ask how long something has left playing, it'll also tell you when it will end according to your local wall-clock time.

Setting `scheme` to `https` allows you to talk to your [Kodi](https://kodi.tv) box securely, but this requires some work on your end to set up.

By default, the skill allows very generic queries such as, `play 99 red balloons` or `shuffle the office`.  These very generic commands can be slow however, and may cause timeouts.  If these timeouts bother you, you can direct the skill to provide help playing media more specifically instead when it encounters these kinds of requests, by disabling `deep_search`.

# Optimising search performance on large libraries (self-host only)

Matching what Alexa heard with content in your library isn't an exact science, and kodi-alexa uses fuzzy matching to try and help to do this reliably. It's possible if your libary is large that this may be a little slower than you'd like. If this is the case it's possible to improve the performance of the fuzzy matching module by installing the python-Levenshtein library. As it's compiled C you'll need to ensure you have python headers available on your machine and the tools required on your OS to compile the module. Using the Levenshtein module has only been tested when running the skill locally as a WSGI script. If all of the above is applicable to your deployment, you can opt to use this optimisation.

In order to include the optional module add the following line to `requirements.txt`:

`python-Levenshtein`


# Performing voice commands

Here are a few demo videos showing how to use it. Other commands you can do are in the utterances file.

[![Amazon Echo - Kodi integration (demo 1) ](http://i.imgur.com/BrXDYm6.png)](https://www.youtube.com/watch?v=Xar4byrlEvo "Amazon Echo - Kodi integration (demo 1) ")

[![Amazon Echo - Kodi integration (demo 2) ](http://i.imgur.com/gOCYnmE.png)](https://www.youtube.com/watch?v=vAYUWaP3EXA "Amazon Echo - Kodi integration (demo 2) ")

[![Amazon Echo - Kodi integration (demo 3) ](http://i.imgur.com/8UZbRMh.png)](https://www.youtube.com/watch?v=4xrrEkimPV4 "Amazon Echo - Kodi integration (demo 3) ")


# Getting help

If you run into an actual issue with the code, please open an Issue here on Github. If you need help getting a server going or configuring the Skill, please visit the [support thread on the Kodi forum.](http://forum.kodi.tv/showthread.php?tid=254502)

# Developer discussion

If you're interested in chatting with us about the development of the skill, we are on [Slack](https://kodi-alexa-slack.herokuapp.com/).
