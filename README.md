# Scrimbot

A discord bot for organising 8-man group events using threads. Built for EchoVR Discord communities.

The bot is written in Python and has a dockerfile included in this repo to easily get it up and running. If you use
docker compose an [example compose file](examples/docker-compose.yaml) can be found in examples.

## Configuration

The bot needs two files in ./data

### bot.token

This should be a plain text file containing the bot token.

### config.yaml/config.json

This should be a yaml or json file containing the settings for the bot. Settings are on a per-server basis. If you plan
to support multiple servers you can add multiple of these blocks. A [config file example](examples/config.yaml) can be
found in the examples.

