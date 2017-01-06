# Contributing Guide

## Please Read
If you would like to contribute, please keep the following in mind:
 - If you make a change that affects the setup (ex. Adding a new custom slot type), make sure you're updating the README file.
 - If you make a new intent, make sure that you follow the same syntax as the rest of the templates. DO NOT just put English text in `alexa.py` file.
   - Make sure you look at the translating guide below to get your intent ready for translation.

## Needs
 - Translation help! If you are a native German speaker, please help with getting the skill translated. I have the responses for cards and voice 'translated' using Google voice, but this needs review. I also need help with getting the utterances translated. Please look at the translating guide below to get setup.
 - New features and refactoring. Please test all code extensively before you commit.


## Translating
To start translation work, you need to have all the proper tools installed. The easiest way to get going is to just do a `pip install -r requirements.txt` (If you are using Lambda, make sure you are in your virtualenv).

To create an updated translation file, run the following command (if you updated templates.yaml): `pybabel extract --mapping babel.cfg -o messages.pot .` and then `pybabel update -i messages.pot -d translations`. This will create an updated version of `translations/de/LC_MESSAGES/messages.po`

If you update the `translations/de/LC_MESSAGES/messages.po` file, run this afterwards: `pybabel compile -d translations`

