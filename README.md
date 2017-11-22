# Alexa Integration With Kodi

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Contents**

- [About](#about)
  - [Kodi-Alexa in Action](#kodi-alexa-in-action)
  - [Supported Commands](#supported-commands)
  - [Getting Help](#getting-help)
  - [Upgrading From a Previous Version](#upgrading-from-a-previous-version)
- [Installation](#installation)
  - [Initial Computer Setup](#initial-computer-setup)
  - [Kodi Setup](#kodi-setup)
    - [Note regarding MySQL and performance](#note-regarding-mysql-and-performance)
  - [Obtaining Your Internet Address](#obtaining-your-internet-address)
  - [Router Setup](#router-setup)
- [Skill Deployment](#skill-deployment)
  - [Choosing a Deployment Method for the Skill](#choosing-a-deployment-method-for-the-skill)
  - [Heroku](#heroku)
    - [Pricing](#pricing)
    - [Limitations](#limitations)
    - [Setup](#setup)
  - [Docker](#docker)
    - [Setup](#setup-1)
  - [AWS Lambda](#aws-lambda)
    - [Pricing](#pricing-1)
    - [Setup](#setup-2)
  - [Self Hosting](#self-hosting)
- [Skill Setup](#skill-setup)
  - [Skill Information](#skill-information)
  - [Interaction Model](#interaction-model)
  - [Configuration](#configuration)
  - [SSL Certificate](#ssl-certificate)
  - [Testing](#testing)
- [Additional Validation of Requests](#additional-validation-of-requests)
- [Extra Settings for More Functionality](#extra-settings-for-more-functionality)
- [Controlling More Than One Instance of Kodi](#controlling-more-than-one-instance-of-kodi)
  - [Getting the device IDs](#getting-the-device-ids)
- [Caching Responses](#caching-responses)
  - [Choosing a Backend](#choosing-a-backend)
  - [Security Considerations](#security-considerations)
  - [Configuring for Amazon S3](#configuring-for-amazon-s3)
  - [Configuring for ownCloud or nextCloud](#configuring-for-owncloud-or-nextcloud)
- [Developer Discussion](#developer-discussion)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# About Kodi-Alexa

This is a skill for Amazon Alexa that allows you to control one or more instances of [Kodi](https://kodi.tv) with your voice.

The process of setting up the skill may seem daunting at first, but the reward -- we feel -- is well worth the effort.  If you carefully follow the directions to the tee, you might find it is not as complicated as it seems.

Unfortunately, as of this moment, we cannot simply ship this skill normally as other skills on Amazon's skill marketplace.  The main technical hurdle is that some features we would need are currently only supported in the US region.  Beyond that, there is the consideration of cost for hosting the skill and the associated database backend.  Do try to keep in mind that this is a hobby project for the developers -- we do not get paid in any way.

However, we have made every effort to here to provide clear and concise documentation to allow you to make use of this skill now.

## Kodi-Alexa in Action

[![Amazon Echo - Kodi integration (demo 1) ](http://i.imgur.com/BrXDYm6.png)](https://www.youtube.com/watch?v=Xar4byrlEvo "Amazon Echo - Kodi integration (demo 1) ")

[![Amazon Echo - Kodi integration (demo 2) ](http://i.imgur.com/gOCYnmE.png)](https://www.youtube.com/watch?v=vAYUWaP3EXA "Amazon Echo - Kodi integration (demo 2) ")

## Supported Commands

Most everything you can do with a remote or keyboard is supported in the skill, and more:

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
- Play trailer for a movie in your library (**requires plugin.video.youtube addon**)
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
- Search for something in your library (**requires script.globalsearch addon**)
- Execute addons
- Shutdown/reboot/sleep/hibernate system
- Toggle fullscreen
- Eject media

Instead of providing the exact verbiage here for each command, we strive to make the experience as natural as we can.  Simply try asking for what you want in a way that feels _right_ to you.  If a particular phrase doesn't work and you think it should, see [Getting Help](#getting-help) to notify us and we will see what we can do to accommodate the phrase you prefer.


## Getting Help

If you need help getting a server going or configuring the Skill, please visit the [support thread on the Kodi forum](http://forum.kodi.tv/showthread.php?tid=254502).

If you run into an actual issue with the code, please open an Issue here on Github; however, most issues you might run into will be a result of the complexity of the installation, so we urge you to first search the [support thread](http://forum.kodi.tv/showthread.php?tid=254502) for your issue.  If you cannot find a resolution for your issue with a search, post there and someone will help you determine if your problem lies within the skill code or your particular configuration.

## Upgrading From a Previous Version

Upgrading the skill from a previous version includes a lot of the initial setup described here, with a few exceptions and a few additional considerations.  Therefore, **it is very important** that you consult the additional documentation in [UPGRADING.md](UPGRADING.md) before you attempt to update the skill.


# Installation

## Initial Computer Setup

Unless you are going to host the skill on [Heroku](https://heroku.com/), there are a few things you will need to install before you can get started:

- [Python 2.7.x](https://www.python.org/downloads/) **(Python 3 is not supported)**
- [Git](https://git-scm.com/downloads/)

## Kodi Setup

Before a command from Alexa can be sent to [Kodi](https://kodi.tv), you need to enable the following settings found under _Settings -> System -> Services -> Web server_ in [Kodi](https://kodi.tv):

- Allow remote control via HTTP
- Allow remote control from applications on this system
- Allow remote control from applications on other systems

Note that wording might change depending on the version of [Kodi](https://kodi.tv) you have installed.  This example is for [Kodi](https://kodi.tv) 17:

![Kodi settings](http://i.imgur.com/YMqS8Qj.png)

Next, supply a _Username_ and _Password_ that you don't use anywhere else.  You can share these credentials with all of your [Kodi](https://kodi.tv) installations, but you should not use the same credentials you might use elsewhere on the web.

Repeat this for every installation of [Kodi](https://kodi.tv) you have that you wish to control via the skill.  All of this information -- including the port number -- can be the same for every installation of [Kodi](https://kodi.tv) if you wish.  If you are unsure, set up every instance of [Kodi](https://kodi.tv) the same way to avoid confusion.

Unless you have a very specific reason to do so, there is no reason to change the port number from the default.  Your router will control access from the outside world.

_Make note of the port, username, and password you are using for later steps._

_If you have more than one instance of [Kodi](https://kodi.tv) you would like to control with this skill, make note of the private IP address for each machine as well.  Private IP addresses are typically addresses like 192.168.1.9 or 192.168.0.23_

### Note regarding MySQL and performance

If you are using [MySQL](https://www.mysql.com) as a database backend for [Kodi](https://kodi.tv), please note that there are known issues with the optimizer in [MySQL](https://www.mysql.com) 5.7.6+ that will cause any commands that involve queueing items in bulk to be tremendously slow.  There is nothing in the skill we can do to fix this, as it is technically a [MySQL](https://www.mysql.com) bug/limitation; however, you can either stay on [MySQL](https://www.mysql.com) < 5.7.6 or you can easily migrate to another that doesn't have this problem, such as [MariaDB](https://mariadb.org).

As far as we are aware, [SQLite](https://sqlite.org) (the default) and [Emby](https://emby.media) do not share this issue.

## Obtaining Your Internet Address

This skill is hosted in the "cloud," unless you opt to host it yourself locally.  As such, it will need to know your internet address to contact [Kodi](https://kodi.tv).

While you can use your [public IP address](http://www.whatsmyip.org/), with most residential internet providers this address can change over time, which would necessitate setting up the skill again.

To avoid this, before you continue, we suggest you set up what's called a _Dynamic Domain Name_ with a service provider such as [Dynu](http://www.dynu.com/).  HowToGeek.com provides a [guide for setting this up](https://www.howtogeek.com/66438/how-to-easily-access-your-home-network-from-anywhere-with-ddns/).

Whether you choose to use your [public IP address](http://www.whatsmyip.org/) or obtain a dynamic domain name, _make note of it before continuing_.

## Router Setup

Unless you are hosting the skill locally, it is required that you have the [Kodi](https://kodi.tv) web server(s) opened up to the internet via port forwarding on your router.

For each [Kodi](https://kodi.tv) instance, you will need a port forwarding rule on your router.  For each _private_ IP address (i.e., the local address of each machine on which [Kodi](https://kodi.tv) is installed), you need to forward a unique _external_ port to that _private_ IP address on your router.

If you followed our suggestion and set up all of your [Kodi](https://kodi.tv) instances with the default port, you would forward them all like so:

- Kodi1: external port 8080, internal -> 192.168.1.10:8080
- Kodi2: external port 8081, internal -> 192.168.1.11:8080
- Kodi3: external port 8082, internal -> 192.168.1.12:8080

And so on for each instance of [Kodi](https://kodi.tv) that you wish to control via the skill.  The key here is that the _external port number_ needs to be unique for each instance.

For more information on port forwarding, see this [HowToGeek guide](https://www.howtogeek.com/66214/how-to-forward-ports-on-your-router/).

# Skill Deployment

## Choosing a Deployment Method for the Skill

When you ask an Amazon Alexa skill to do anything, it ultimately contacts another web server which executes code to process your request.  This skill isn't any different, and needs such a server as well.

You have a few choices, ordered by difficulty:

- [Heroku](#heroku)
- ~~[Docker](#docker)~~
- [AWS Lambda](#aws-lambda)
- [Self-host](#self-hosting)

Do note that while [Heroku](https://heroku.com/) is the easiest to setup, it does lack some features, such as support for multiple installations of [Kodi](https://kodi.tv).  If that is unimportant to you, we definitely recommend that you choose that deployment method.

## Heroku

### Pricing
[Heroku](https://heroku.com/) is a great way to get a server running for free, but there is a small limitation with the free tier on Heroku where the 'dyno' will go to sleep after 30 minutes of in-activity. This might cause some commands to timeout, but so far it seems to be the best option for getting up and running as quickly as possibly. To get around this, you can either pay for a "Hobby" server which is only $7/month. If you really don't want to pay, there is a work-a-round where you get enough free hours per month to leave the server running 24/7 if you add your Credit Card to your account. Then you can use something like [Kaffeine](http://kaffeine.herokuapp.com/) to keep it from spinning down.

### Limitations
Currently we do not support [addressing multiple instances](#controlling-more-than-one-instance-of-kodi) of [Kodi](https://kodi.tv) with [Heroku](https://heroku.com/).  If you wish to control multiple instances of [Kodi](https://kodi.tv), you will need to set up multiple copies of the skill to do so.

### Setup
After you have set up an Heroku account, click on this button below to provision a new server. Select a unique name to make upgrades easy.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy/?template=https://github.com/m0ngr31/kodi-alexa)

_Make note of the endpoint_

Now skip ahead to [Skill Setup](#skill-setup).


## Docker
### Setup
_Coming soon_.


## AWS Lambda
### Pricing
Lambda is a great service which lets the skill run "serverless." AWS provides credits for new accounts and should allow you to run everything the skill needs for free for 12 months. Once you are being billed for it, it will be less than $0.20/month. Very reasonable for what it offers.

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

Next you need to create the file `kodi.config` from the [kodi.config.example template](https://raw.githubusercontent.com/m0ngr31/kodi-voice/master/kodi_voice/kodi.config.example) and enter the correct information for: address, port, username, and password. I'll go over the other variables in another section below.

After you've created your config file, run `pip install -r requirements.txt` and `pip install packaging zappa lambda-packages`.

Before you can send any code to Lambda, you'll need to set up Zappa. Just run `zappa init` and accept the defaults for everything. If it doesn't automatically detect that this is a Flask app, tell it that the application function is `alexa.app`.

To make an initial deployment to Lambda, just run the following command: `zappa deploy dev`. It'll take a few minutes, and at the end it will give you a URL that you will need to copy. It will look like this:
![Lambda deploy](http://i.imgur.com/5rtN5ls.png)

You are now running on Lambda! To update after there is a change here, or you updated your env variables, see the instructions in [UPGRADING.md](UPGRADING.md).

Now skip ahead to [Skill Setup](#skill-setup).


## Self Hosting

If you are savvy enough to run your own web server, this is just a bog-standard WSGI app, and you're free to host it on any web server, provided it supports HTTPS.  You will have to generate your own SSL certificate, be it self-signed or via a Certificate Authority (CA), such as [Let's Encrypt](https://letsencrypt.org/).  This is an Amazon requirement.

You will need to create the file `kodi.config` from the [kodi.config.example template](https://raw.githubusercontent.com/m0ngr31/kodi-voice/master/kodi_voice/kodi.config.example).  The template file contains comments to describe the options.

Install the modules in `requirements.txt`.

Now skip ahead to [Skill Setup](#skill-setup).


# Skill Setup

Once you've set up your server, you'll need to configure an Interaction Model for your skill.

If you don't yet have an Amazon Developer account, you'll need to create one by [visiting here](https://developer.amazon.com/login.html) and logging in with your usual Amazon credentials.  Fill in the required fields, agree to the terms, and answer, "No," when asked if you're going to monetize your apps.

Then, head over to the [Skills list on Amazon's developer page](https://developer.amazon.com/edw/home.html#/skills/list) and hit the _Add new skill_ button.

## Skill Information

![Inital setup skill](http://i.imgur.com/AzufQxo.png)

For _Skill Type_, choose **Custom Interaction Model**.

For _Language_, choose your native language.

For _Name_, enter **Kodi**.

For _Invocation Name_, you can choose whatever you like.  **kodi** works well for us, but it can be whatever you'd like for the phrase:

`alexa, tell invocation_name to ...`

Leave everything else at their default values.

## Interaction Model

This is the model that Alexa will use to pass information to the skill that we've deployed earlier.

The Model consists of Slots, an Intent Schema, and Sample Utterances.

You need to first create the Slots that contain the library items in [Kodi](https://kodi.tv), broken up into categories for the skill.  It is not necessary to keep these up-to-date after the initial setup of the Interaction Model.

To establish initial Slot values, you can use [this webapp](https://slot-generator.herokuapp.com/) and point it at the instance of [Kodi](https://kodi.tv) that has the largest number of items in its library.

You can also get the information from running `python generate_custom_slots.py` in the project directory, assuming you have a local copy of the code and proper configuration in `kodi.config`.  This will communicate with the [Kodi](https://kodi.tv) instance defined in the `[DEFAULT]` section in `kodi.config` and generate a series of files from which you can create your Slots.

For each Slot, you need to click `Add Slot Type`, name it according to the output from one of the above generators, and fill the values with their contents.

Ultimately, you will end up adding the following Slots:

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

_If one of your slots is empty, you can just enter the word 'Empty' or something so that it'll save._

Next, you'll have to paste the contents of [IntentSchema.json](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/IntentSchema.json) into the _Intent Schema_ field.

Then, paste the contents of [SampleUtterances.en.txt](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/SampleUtterances.en.txt) or [SampleUtterances.de.txt](https://raw.githubusercontent.com/m0ngr31/kodi-alexa/master/speech_assets/SampleUtterances.de.txt), depending on your native language, in the _Sample Utterances_ field.

![2nd tab](http://i.imgur.com/WQYExdK.png)

## Configuration

Enter your endpoint here.  It will always be `HTTPS` and you should choose a region that is geographically close to you:

![3rd tab](http://i.imgur.com/GjFvKYv.png)

## SSL Certificate

If you are using Heroku or Lambda, select the middle option:

![4th tab](http://i.imgur.com/moGJQrx.png)

If you are self-hosting, select one of the outer options depending on how you've chosen to generate your certificate.

## Testing

Setup is complete at this point.

From here, you can use the simulator or any other Alexa-enabled device to test requests.  Note that the simulator has a few nuances and isn't identical to an actual device, so if a request fails in the simulator, please try it on a real Alexa-enabled device.

If you can't manage to get valid responses at this point, see the [Getting Help](#getting-help) section.


# Additional Validation of Requests

To verify that incoming requests are only allowed from your own copy of the skill, you can set the `skill_id` configuration variable to your own Application ID; e.g., `amzn1.ask.skill.deadbeef-4e4f-ad61-fe42-aee7d2de083d`

# Extra Settings for More Functionality

Setting the `timezone` configuration variable will make it so when you ask how long something has left playing, it'll also tell you when it will end according to your local wall-clock time.

Setting `scheme` to `https` allows you to talk to [Kodi](https://kodi.tv) securely, but this requires that you set up a reverse HTTPS proxy.

By default, the skill allows very generic queries such as, `play 99 red balloons` or `shuffle the office`.  These very generic commands can be slow however, and may cause timeouts.  If these timeouts bother you, you can direct the skill to provide help playing media more specifically instead when it encounters these kinds of requests, by disabling `deep_search`.

# Controlling More Than One Instance of Kodi

As of version 2.6 of the skill, it can now control more than one instance of [Kodi](https://kodi.tv).  The skill determines which instance to talk to by determining which Echo device received the command.

You set up the mapping in the `kodi.config` file. There are a few examples there with dummy device IDs.

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

# Caching Responses

Every time you make a request to find and/or play a media item, the skill will ask [Kodi](https://kodi.tv) for all of the media items it has in its library of that media type.  For example, if you have a song library of 30,000 items and you ask for a particular song, the skill must retrieve the 30,000 songs from your library to match what you asked for with what you have.

As you can imagine, sending such a large response over the internet to your skill can take some time.  How long this takes is a function of your available internet upload bandwidth vs how large your library is.

For those with particularly large libraries or very slow uplinks, we provide the option to cache these responses somewhere closer to the skill.

When utilizing caching, you will need to make a voice request to clear out the old cache objects every time you make changes to your [Kodi](https://kodi.tv) library.  'Changes' include adding a new item, removing an item, or editing an item.  In practice, most people simply add and remove items in their libraries, which requires instructing [Kodi](https://kodi.tv) to notice the changes anyway.  So, if you get into the habit of using voice requests for this:

```
Alexa, ask Kodi to clean library
Alexa, ask Kodi to update library
```

everything will sort itself out.  If you forget to use the voice commands after a library change, the skill will not pick up your changes/additions.  In this case, just re-do the library update/clean via voice.

The configuration for the cache buckets is defined in the [device sections](#controlling-more-than-one-instance-of-kodi) of `kodi.config`.  This allows you to use more than one bucket if you wish to do so.  It is not necessary though even if you have more than one [Kodi](https://kodi.tv) library: each cache object is named such that they won't collide.  However, the `clean library` and `update library` commands will clear out all objects in the bucket -- even those that don't pertain to the library you're updating or cleaning.  Therefore, it is up to you to decide if it's worth the extra configuration effort to use more than one bucket.

_If you only have one library or you are unsure, it will be simplest to just use one bucket by defining all of the cache configuration in the_ `[DEFAULT]` _section of_ `kodi.config`.

## Choosing a Backend

*Regardless of the location where you store the cached responses, bear in mind that you may incur charges to do so.*

We allow storage of cache objects currently in either an [Amazon S3 bucket](http://docs.aws.amazon.com/AmazonS3/latest/gsg/GetStartedWithS3.html) or on an [ownCloud](https://owncloud.org)/[nextCloud](https://nextcloud.com) server.

For most people, an [Amazon S3 bucket](http://docs.aws.amazon.com/AmazonS3/latest/gsg/GetStartedWithS3.html) will be the right choice here.  But please note that [Amazon may charge you for this service](https://aws.amazon.com/s3/pricing/).  It is very inexpensive, however, and it's highly likely that you'll fall under the Free Usage Tier if you're only using it for this skill.

For [Heroku](#heroku) users and those [self-hosting](#self-hosting) the skill, the backend you choose will mostly depend on which ends up being faster for you and whether or not your usage falls under the free tier for [Amazon S3](http://docs.aws.amazon.com/AmazonS3/latest/gsg/GetStartedWithS3.html).  If cost is not a consideration, feel free to try all backends and see what works best for you.

If you are [self-hosting](#self-hosting) the skill local to your [Kodi](https://kodi.tv) installation(s), you may wonder if this has any benefit for you.  It will, if you already have or want to set up an [ownCloud](https://owncloud.org)/[nextCloud](https://nextcloud.com) server local to your [Kodi](https://kodi.tv) installation(s).  Since the requests the skill makes to [Kodi](https://kodi.tv) involve a database query as well as the hit to its relatively-slow-web-server, retrieving the responses from a cache can shave off a little time.  How much really depends on your hardware and database configuration; the difference will probably be small, but if you've read this far, such an optimization might be worth the effort for you.

## Security Considerations

For all cache backends, you should use credentials that only provide access to the cache bucket and nothing else.  The primary concern here is that the credentials are stored in `kodi.config`, which is stored in your skill deployment.  If you can't secure the skill deployment, you should create a user that _only_ has access to the cache.

A secondary consideration is that this can put your library items in public view.  The cache objects themselves will not directly divulge personally identifying information, but your account credentials can tie the data to you if someone gained access to them.

## Configuring for Amazon S3

The first thing you need to do is [sign up for Amazon S3](http://docs.aws.amazon.com/AmazonS3/latest/gsg/SigningUpforS3.html) if you haven't already.  Next, [create a unique bucket](http://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html) in which the skill can store cache objects.  It is recommended that you use a randomized name for the bucket if possible.

For the bucket you create, you definitely should not use your root credentials, and ideally, you shouldn't use admin credentials either.  If you deployed the skill via [AWS Lambda](#aws-lambda), 'admin credentials' would be the the keys for the `kodi-alexa` user described there.

It would be best to [create another user with only the ability to list buckets and administer the cache bucket](http://mikeferrier.com/2011/10/27/granting-access-to-a-single-s3-bucket-using-amazon-iam/) via the [IAM Management Console](https://console.aws.amazon.com/iam/home).

However, if you don't use S3 for anything else that you consider important or private, you're welcome to use the `kodi-alexa` user credentials for the rest of this.

For each bucket you have created, you will need to add the following to either the `[DEFAULT]` section or the appropriate [device section](#controlling-more-than-one-instance-of-kodi):

```
cache_bucket = your_bucket_name
s3_cache_aws_access_key_id = your_access_key_id
s3_cache_aws_secret_access_key = your_secret_key
```

For example:

```
[DEFAULT]
cache_bucket = kodi-alexa-7ce4fea901
s3_cache_aws_access_key_id = AKQJ56NSL3XGGLQYDT0L
s3_cache_aws_secret_access_key = iCmj7ag+mdxkcDLcst/gAMDXrjkp0j7toMMDrrkJ

# Office Echo Dot
[amzn1.ask.device.AEFDXCGLSFJFNGCVF8SDJF90FID9G284JDJFGJGHH83358DJFFGIGD734JJDFGK211GDFFHHH23HGFJTYEFGJRT56KJDHDFJ5546DJDFFSWOPPP677P88P873EHZNZDFEIRTYIN2239NDFGIH724JDFKS2AA]
cache_bucket = kodi-alexa-4fae019a1f
```

## Configuring for ownCloud or nextCloud

You will need to provide credentials for a user that can create the bucket (folder/directory) that you specify at the root of each URL you provide.

For each bucket, you will need to add the following to either the `[DEFAULT]` section or the appropriate [device section](#controlling-more-than-one-instance-of-kodi):

```
cache_bucket = your_bucket_name
owncloud_cache_url = https://my.owncloudserver.com/owncloud/
owncloud_cache_user = username
owncloud_cache_password = password
```

For example:

```
[DEFAULT]
cache_bucket = kodi-alexa-7ce4fea901
owncloud_cache_url = https://my.owncloudserver.com/owncloud/
owncloud_cache_user = username
owncloud_cache_password = password

# Office Echo Dot
[amzn1.ask.device.AEFDXCGLSFJFNGCVF8SDJF90FID9G284JDJFGJGHH83358DJFFGIGD734JJDFGK211GDFFHHH23HGFJTYEFGJRT56KJDHDFJ5546DJDFFSWOPPP677P88P873EHZNZDFEIRTYIN2239NDFGIH724JDFKS2AA]
cache_bucket = kodi-alexa-4fae019a1f
```

# Developer Discussion

If you're interested in chatting with us about the development of the skill, we are on [Slack](https://mediacenterio-slack.herokuapp.com/).
