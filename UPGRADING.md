# Upgrading

For each new update, please run the Slot generator again and repopulate all of your slots with the output. If you don't do this, the skill might seem to successfully build and save, but those with large libraries may encounter issues at runtime. There might be new slots needed for new functionality as well.

Also remember to always update the Intents and Utterances in the skill. If new slots were added, you will need to add those as well.

## Heroku

Just delete the existing app from your Heroku Dashboard, and create another with the button below with the same name you gave earlier.
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy/?template=https://github.com/m0ngr31/kodi-alexa)

## AWS Lambda

If you are not using Zappa yet, please go back to the README file there and start from scratch. If you are already using Zappa, browse to the application directory in your terminal, make sure that your virtual environment is enabled and run `pip install -r requirements.txt`, `git pull origin master`, and `zappa update dev`.
