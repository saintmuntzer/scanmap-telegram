# [@scanmapchi](https://twitter.com/scanmapchi) Telegram Relay

Telegram script for https://scanmap.mobi/chi. Forked from [scanmap-twitter](https://github.com/kalilsn/scanmap-twitter), which was itself based on the [scanmapny](https://twitter.com/scanmapny) bot.

## Configuration

Create `config.py`:
`cp config.example.py config.py`

Update the configuration with the following information.

- `TELEGRAM_TOKEN` - Telegram Bot API token provided by [BotFather](https://t.me/botfather)
- `TELEGRAM_CHAT` - chat ID of the group, channel, or user you want the messages sent to
- `SITE_URL` - URL for your Scanmap site
- `SITE_NAME` - name of your Scanmap site
- `LOG_URL` - URL for your Scanmap site's JSON-formatted logs
- `HASHTAGS` - any hashtags you want added to the Telegram messages; can be left blank
- `DAEMON` - run as long running process if set to True. defaults to False if unset
- `UPDATE_INTERVAL` - an integer of seconds to wait between checking for updates. defaults to 30 if unset. this is only used in while running in daemon mode.

## Usage

Running `main.py` will send the log entries that have been added since the timestamp in `./last_update`. If `./last_update` is not found, the script will just tweet the most recent entry.

### With docker

Build the image:
`docker build -t scanmapchi .`

Execute:
`docker run -v "$(pwd):/usr/src/app" scanmapchi`

### Without docker

Requires Python 3.6+

Install python modules:
`pip3 install -r requirements.txt`

Execute:
`python3 main.py`

## License

Licensed under the [Anti-Capitalist Software License (ACSL)](https://anticapitalist.software/). See the `LICENSE` file for full statement.
