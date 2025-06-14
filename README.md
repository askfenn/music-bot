~~Bot doesn't work (yet :tm:)~~

Actually works :anguished:

# Setup

First do  discord bot setup in [Discord Developer Portal](https://discord.com/developers/applications) and copy bot token.

Create a `.env` file and paste the bot token. [Example](https://github.com/askfenn/music-bot/blob/master/.env.example)

Then:

`python -m venv venv`

`./venv/Scripts/Activate.ps1`

`pip install -r requirements.txt`

`python music_bot.py`

# Usage

`!play <youtube URL or search>`: Plays whatever URL is provided or searches and plays the top result

`!pause`: Pause (duh)

`!resume`: Resumes playing

`!skip`: Skip current song

`!now`: See what song is playing now

`!stop`: Stop playing and empty queue

`!join`: Joins channel

`!leave`: Leaves channel
