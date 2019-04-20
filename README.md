# Kanzi: Alexa Integration With Kodi

[![Build Status](https://travis-ci.org/m0ngr31/kanzi.svg?branch=master)](https://travis-ci.org/m0ngr31/kanzi)

<p align="center">
  <img src="https://i.imgur.com/k0MOv2r.png" width="200"/>
</p>

## Documentation
Visit the [documentation here](https://lexigr.am) to learn how to setup this skill.

## About
This is a skill for Amazon Alexa that allows you to control one or more instances of [Kodi](https://kodi.tv) with your voice.

The process of setting up the skill may seem daunting at first, but the reward -- we feel -- is well worth the effort.  If you carefully follow the directions to the tee, you might find it is not as complicated as it seems.

Unfortunately, as of this moment, we cannot simply ship this skill normally as other skills on Amazon's skill marketplace.  The main technical hurdle is that some features we would need are currently only supported in the US region.  Beyond that, there is the consideration of cost for hosting the skill and the associated database backend.  Do try to keep in mind that this is a hobby project for the developers -- we do not get paid in any way.

However, we have made every effort to here to provide clear and concise documentation to allow you to make use of this skill now.

### Supported Commands
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

### Kanzi in Action
<p>
  <a href="https://www.youtube.com/watch?v=Xar4byrlEvo">
    <img src="https://i.imgur.com/BrXDYm6.png" style="max-width: 500px">
  </a>
</p>

<p>
  <a href="https://www.youtube.com/watch?v=vAYUWaP3EXA">
    <img src="https://i.imgur.com/gOCYnmE.png" style="max-width: 500px">
  </a>
</p>

## Getting Help
If you need help getting a server going or configuring the Skill, please visit the [support thread on the Kodi forum](http://forum.kodi.tv/showthread.php?tid=254502).

If you run into an actual issue with the code, please open an Issue here on Github; however, most issues you might run into will be a result of the complexity of the installation, so we urge you to first search the [support thread](http://forum.kodi.tv/showthread.php?tid=254502) for your issue.  If you cannot find a resolution for your issue with a search, post there and someone will help you determine if your problem lies within the skill code or your particular configuration.

## Contributors
I would like to thank and name all the contributors who have donated their precious time and talents to improving this skill:
 - [ausweider](https://github.com/ausweider)
 - [digiltd](https://github.com/digiltd)
 - [ghlynch](https://github.com/ghlynch)
 - [jagsta](https://github.com/jagsta)
 - [jingai](https://github.com/jingai)
 - [kuruoujou](https://github.com/kuruoujou)
 - [m0ngr31](https://github.com/m0ngr31)
 - [mcl22](https://github.com/mcl22)
 - [nemik](https://github.com/nemik)
 - [ruben0909](https://github.com/ruben0909)

## Donate
[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/lexigram)

## Developer Discussion
If you're interested in chatting with us about the development of the skill, we are on [Slack](https://lexigram-slack.herokuapp.com/).