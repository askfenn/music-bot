Bot doesn't work (yet :tm:)

First do  discord bot setup in [Discord Developer Portal](https://discord.com/developers/applications) and copy bot token.

Create a `.env` file and paste the bot token. [Example](https://github.com/askfenn/music-bot/blob/master/.env.example)

Then:

`python -m venv venv`

`./venv/Scripts/Activate.ps1`

`pip install -r requirements.txt`

`python music_bot.py`
