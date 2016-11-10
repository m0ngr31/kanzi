# Alexa integration with Kodi

I'm forking the base code off of [this project from Maker Musings](http://www.makermusings.com/2015/08/22/home-automation-with-amazon-echo-apps-part-2). It originally supported checking to see how many new episodes there are and you can ask it if there are any new episodes for a certain show.

I've expanded it to support the following features:

- Basic navigation (Up/Down, Left/Right, Page Up/Down, Select, Back, Open Menu)
- Playback control (Play/Pause, Skip, Previous, Stop)
- Shuffle music by artist
- Play random unwatched episode of TV show
- Play random unwatched movie
- Play random movie from a specific genre
- Play specific episode of a TV show ('Play season 4 episode 10 of The Office')
- Play specific movie
- Continue watching next episode of last show that was watched
- Play next episode of a show
- Play newest episode of a show
- Clean/Update video and audio sources
- "What's playing?" functionality for music, movies, and TV SHOWS
- Searching for something in your library
- "Party mode" for music (shuffle all)
- Play audio playlists
- Play specific album

## Kodi Setup

Before you can do anything, you need to enable the "Allow remote control via HTTP", "Allow remote control from applications on this system", and "Allow remote control from applications on other systems" options in your Kodi settings. (Note that wording might be change a little bit on different versions, this example is for Kodi 17).

![Kodi settings](http://i.imgur.com/YMqS8Qj.png)

Make sure to keep track of the port, username, and password you are using. Now, you'll need to have your Kodi box opened up to the internet via port forwarding. If you don't have a dedicated IP address, you'll need a dynamic DNS service to give you a static URL to use so you don't have to be constantly change this value.

Once you get that setup, you'll have to have your own server to handle the requests and pass them to your Kodi box. Since this is a Python application, it has several ways that you can run it.

Here are a few options to get started:

- [Heroku](#heroku)
- [AWS Lambda](#aws-lambda)
- [Docker](#docker)

If you plan on running your own Apache/Nginx server, I'm sure you can figure that out yourself. Skip ahead to the [Skill setup section](#skill-setup).

## Heroku

[Heroku](https://heroku.com/) is a great way to get a server running for free, but there is a small limitation with the free tier on Heroku where the 'dyno' will go to sleep after 30 minutes of in-activity. This might cause some commands to timeout, but so far it seems to be the best option for getting up and running as quickly as possibly. To get around this, you can either pay for a "Hobby" server which is only $7/month. If you really don't want to pay, there is a work-a-round where you get enough free hours a month to leave this server running 24/7 if you add your Credit Card to your account. Then you can use something like [Kaffeine](http://kaffeine.herokuapp.com/) to keep it from spinning down.

After you've setup an Heroku account, go ahead and [install the command line tool](https://toolbelt.heroku.com/). Once installed, open up a command line and run `heroku login`.

To create a new app, just run this from the command line: `heroku apps:create`. If that runs successfully, you'll see something like this:
![Create app](http://i.imgur.com/C17Ts7L.png)

Now, clone my repo: `git clone https://github.com/m0ngr31/kodi-alexa.git` and `cd kodi-alexa`.

Once you have my repo cloned and you are in the directory, you can setup the following environment variables to talk to your Kodi box:

- KODI_ADDRESS
- KODI_PORT
- KODI_USERNAME
- KODI_PASSWORD

You can do this easily from the command line: `heroku config:set KODI_ADDRESS='your_ip_or_dynamic_address' KODI_PORT='kodi_port' KODI_USERNAME='kodi_username' KODI_PASSWORD='kodi_password' --app app-name-and-number`. Changing of course for your settings. You can also use the settings page on your Heroku app to add these.

You can also alternatively store configuration in a file called `.env` which you need to create yourself from a copy of `.env.wsgi`

Now run `git remote add heroku https://git.heroku.com/your_apps_name_and_number.git`. This command will allow heroku to deploy new code based on what is in your directory.

Next, run `git push heroku master`. This will push the code to Heroku and deploy the server!

Heroku doesn't just fire up the server automatically, so you have to tell it to: `heroku ps:scale web=1 --app app-name-and-number`. Now you are ready to setup the Alexa skill.

*If I release a new update here, just browse to the repo directory in your terminal, and run these commands: `git pull origin master` and `git push heroku master`*

Now skip ahead to the [Skill setup section](#skill-setup).

## AWS Lambda

I'm not going to talk about what Lambda is, I'll let you [search for that on your own](http://lmgtfy.com/?q=What+is+AWS+Lambda%3F#). On Lambda, the first 1,000,000 requests/month are free, so I doubt you'll ever hit it's limit talking to your Echo.

To deploy to Lambda, we're going to use a great little Python package called [`lambda-deploy`](https://github.com/jimjkelly/lambda-deploy), so you'll have to have Python 2.7 (and pip) installed. If you don't have it installed on your computer already, just install it and come back. There are plenty of guides online to install it on whatever system you're using.

Now, either [download](https://github.com/m0ngr31/kodi-alexa/archive/master.zip) or clone my repo: `git clone https://github.com/m0ngr31/kodi-alexa.git` and `cd kodi-alexa`.

Once you have my repo downloaded and you are in the directory, you can setup the following environment variables to talk to your Kodi box:

- KODI_ADDRESS
- KODI_PORT
- KODI_USERNAME
- KODI_PASSWORD

And several AWS environment variables so we can upload the code to Lambda:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- LAMBDA_ROLE

The environment variables are stored in an `.env` file which you need to create yourself from a copy of `.env.lambda`

**Take care with your `.env` file, it contains access details that you do not want to be uploaded to any public repositories (or pasted in a forum)**

You do not need to change the options that already have values.

If using **eu-west-1** AWS region to host your Lambda function then you can adjust `AWS_DEFAULT_REGION` accordingly.

#### About AWS regions

The AWS documentation ["Creating an AWS Lambda Function for a Custom Skill"](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function) states:

>  _Lambda functions for Alexa skills must be hosted in the US East (N. Virginia) region. Currently, this is the only Lambda region the Alexa Skills Kit supports_.

The above statement is repeated many times throughout the docs.

However it is **outdated information** as now you can also use Ireland (eu-west-1). This has been confirmed by one of our users.

It is also stated on the recently published tutorial["How to Build a Multi-Language Alexa Skill"](https://developer.amazon.com/public/community/post/Tx2XUAQ741IYQI4/How-to-Build-a-Multi-Language-Alexa-Skill):

> _Only eu-west-1 (Dublin) and us-east-1 (N.Virginia) AWS regions currently support the Alexa Skills Kit and lambda integration._

### AWS variables

To get to the options for the AWS variables, log in to the [AWS console](https://console.aws.amazon.com/console/home) and browse to [Identity and Access Management](https://console.aws.amazon.com/iam/home). Once in there, navigate to the "Users" tab and look for an existing user. If there isn't one, go ahead and create a new one. Once you see a user there, click on it and go to the 'Security Credentials' tab. Then click on 'Create Access Key'. This will only show once, so make sure you copy the Access Key and Secret Access Key before you close the modal. Paste these values into the `.env` file.

Next, click on the 'Roles' tab on the right. Here, you're going to create a new role that will be just used for running Lambda functions. What name you give it doesn't matter, but when asked for policies, make sure you select "AWSLambdaFullAccess". After that's been created, copy the "Role ARN" value to the `.env` file under "LAMBDA_ROLE". It'll look something like "arn:aws:iam::11111111111:role/lambda" depending on what you named it.

Now, go back to the console and make sure you are in the directory with this code in it. Run the following commands:

`pip install lambda-deploy`

`python deploy-to-lambda.py`

If you edited the `.env` file correctly, this should have successfully sent the code to AWS. Let's go look at your Lambda functions and finish setting up the function. [Browse back to the AWS console and click on Lambda](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions?display=list). There you should see your function. Click on it and go to the triggers tab. Click on "Add Trigger" and select "Alexa Skills Kit". At the top right of this page, you'll see text that will say something like "ARN - arn:aws:lambda:us-east-1:11111111111:function:kodi-alexa". Copy this, as we'll need it in when you setup the skill.

Now skip ahead to the [Skill setup section](#skill-setup).

## Docker

I personally haven't tried this, so I can't verify that it works, and I don't know how to make it work. But if someone would like to submit a PR to add documentaion, I would appreciate it.

Here the docker command to get it running: `docker run -p "443:8000" -e KODI_ADDRESS="<local xbmc ip>" -e KODI_PORT="8080" -e KODI_USERNAME="<your xbmc/kodi username>" -e KODI_PASSWORD="<the user's password>" kuroshi/kodi-alexa`


# Skill Setup

Once you've setup your server, you'll need to setup an Amazon developer account and start setting up a new Alexa skill.

Here's what it'll look like:

![1st tab](http://i.imgur.com/q0Wqld1.png)

You'll just need to stick the URL from your app in the Endpoint field. If you are using Lambda, you'll need to use the ARN you got earlier.

On the next tab, you'll have to paste the `alexa.intents` file into the "Intent Schema" field, and paste the `alexa.utterances` file in the "Sample Utterances" field. Generate and save your Slots first before pasting the Intents and Utterances to avoid errors when attempting to save.

The tricky part is generating the Slots in the middle section. You need to create 6 different slots:

- MOVIES
- MOVIEGENRES
- SHOWS
- MUSICARTISTS
- MUSICALBUMS
- MUSICPLAYLISTS

To make it as easy as possible, I wrote a little webapp that will give you the information you need: [here.](https://slot-generator.herokuapp.com/). You can also get the information from running `python generate_custom_slots.py` in the repo directory if you have python installed. This will create txt files with the relevant information. If one of your slots is empty, you can just enter the word 'Empty' or something so that it'll save.

![2nd tab](http://i.imgur.com/WQYExdK.png)

The next tab has info about the SSL cert, if you are using Heroku, select the middle option.

![3rd tab](http://i.imgur.com/moGJQrx.png)

After that is pretty much just information that you can just put whatever into. Don't submit it for certification since only you will be using your server.

And now you should be set! Go ahead and try speaking a few commands to it and see if it works! If you can't get it working, try looking for support in [this thread](http://forum.kodi.tv/showthread.php?tid=254502) on the Kodi forum, and if you have more techinical problems, submit and issue here on Github.

Thanks!


# Additional validation of requests

To verify that incoming requests are only allowed from your own copy of the skill, you can set the `SKILL_APPID` environment variable to your own Application ID; e.g., `amzn1.ask.skill.deadbeef-4e4f-ad61-fe42-aee7d2de083d`

*NOTE: The rest of this is unsupported on AWS Lambda as Amazon performs these checks for you.*

You can also enable some extra verification of the SSL certificate by setting `SKILL_VERIFY_CERT` to `true`.  This will perform the following checks on the certificate:

* Incoming request is from Amazon,
* Certificate URL is from Amazon,
* Timestamp of certificate is valid/not expired,
* Signature can be verified.

Note that you will need to manually install the dependencies in `requirements_verify.txt` if you want this additional validation.  Depending on your host environment, something like `pip install -r requirements_verify.txt` might work.


# Optimising search performance on large libraries (local installations only)

Matching what Alexa heard with content in your library isn't an exact science, and kodi-alexa uses fuzzy matching to try and help to do this reliably. It's possible if your libary is large that this may be a little slower than you'd like. If this is the case it's possible to improve the performance of the fuzzy matching module by installing the python-Levenshtein library. As it's compiled C you'll need to ensure you have python headers available on your machine and the tools required on your OS to compile the module. Using the Levenshtein module has only been tested when running the skill locally as a WSGI script. If all of the above is applicable to your deployment, you can opt to use this optimisation.

In order to include the optional module add the following line to `requirements.txt`:

`python-Levenshtein`


# Performing voice commands

Here are a few demo videos showing how to use it. Other commands you can do are in the utterances file.

[![Amazon Echo - Kodi integration (demo 1) ](http://i.imgur.com/BrXDYm6.png)](https://www.youtube.com/watch?v=Xar4byrlEvo "Amazon Echo - Kodi integration (demo 1) ")

[![Amazon Echo - Kodi integration (demo 2) ](http://i.imgur.com/gOCYnmE.png)](https://www.youtube.com/watch?v=vAYUWaP3EXA "Amazon Echo - Kodi integration (demo 2) ")

[![Amazon Echo - Kodi integration (demo 3) ](http://i.imgur.com/8UZbRMh.png)](https://www.youtube.com/watch?v=4xrrEkimPV4 "Amazon Echo - Kodi integration (demo 3) ")


# Getting Help

If you run into an actual issue with the code, please open an Issue here on Github. If you need help getting a server going or configuring the Skill, pleas visit the [support thread on the Kodi forum.](https://forum.kodi.tv/showthread.php?tid=254502)
