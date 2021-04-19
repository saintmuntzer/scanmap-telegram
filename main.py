from datetime import datetime
import requests
import time
import logging

import config

LAST_UPDATE_FILENAME = 'last_update'

LABELS = {
  'alert': '⚠',
  'police_presence': '👮',
  'units_requested': '🚓',
  'fire': '🔥',
  'prisoner_van': '🚐',
  'group': '🚩',
  'injury': '🩹',
  'barricade': '🚧',
  'aviation': '🚁',
  'other': '🔹',
  'aid': '⛑',
  'military': '💂',
  'protestor_barricade': '🛡',
  'arrests': '🚨 ',
}

HASHTAGS = f'\n{config.HASHTAGS}' if hasattr(config, 'HASHTAGS') else ''

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
TELEGRAM_CHAT = config.TELEGRAM_CHAT
SITE_URL = config.SITE_URL
SITE_NAME = config.SITE_NAME
DAEMON = config.DAEMON if hasattr(config, 'DAEMON') else False
UPDATE_INTERVAL = config.UPDATE_INTERVAL if hasattr(config, 'UPDATE_INTERVAL') else 30

APP_STARTUP_TIME = time.time()

last_update_sent = None

# Reads (from file) the timestamp of the last log item sent
# Returns None if not found
def get_last_timestamp():
    global last_update_sent
    if last_update_sent == None:
        try:
            with open(LAST_UPDATE_FILENAME, 'r') as f:
                last_update_sent = float(f.read())
        except FileNotFoundError:
            logging.debug('Last update file not found.')
            pass
        except Exception as e:
            # Treat any kind of error as if we haven't sent updates before
            logging.exception('Error while reading the last update file.')

    return last_update_sent

# Write the given timestamp to a file for reading on the next execution
def save_last_timestamp(timestamp):
    global last_update_sent
    logging.info(f'Updating last update file with timestamp {timestamp}')
    last_update_sent = float(timestamp)
    try:
        with open(LAST_UPDATE_FILENAME, 'w') as f:
            f.write(timestamp)
    except Exception as e:
        logging.exception('Error while writing last update to file.')
        

# Render a log item to a formatted string for Telegram
def format_message(data, timestamp):
    emoji = LABELS.get(data['label'], '')
    label = data['label'].replace('_', ' ').capitalize() if data['label'] != 'other' else ''
    time = datetime.fromtimestamp(float(timestamp)).strftime('%I:%M%p\n%m/%d/%Y')

    return f"{emoji + ' ' if emoji else ''}{label + ' at ' if label else ''}{data['location']}\n{data['text']}\n{HASHTAGS}\n\n{time}\nvia <a href='{SITE_URL}'>{SITE_NAME}</a>"

# Send a log item via Telegram bot and return the timestamp, or None on failure
def send_log_item(log):
    message = format_message(log['data'], log['timestamp'])
    params = {"chat_id": TELEGRAM_CHAT, "text": message, "disable_web_page_preview": True, "parse_mode": "HTML"}
    try:
        requests.request("GET", f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params=params)
    except Exception as e:
        logging.exception('Error while sending scanmap event to Telegram.')
        return None

    return log['timestamp']

# Lookup timestamp of last sent log, then send all new logs to Telegram via send_log_item
# Returns the number of new events successfully sent
def handle_log_batch():
    try:
        response = requests.get(config.LOG_URL)
        parsed_response = response.json()
        logs = parsed_response['logs']
    except Exception as e:
        logging.exception(f"Error while fetching scanmap logs from {config.LOG_URL}")
        return 0
    if len(logs) == 0:
        logging.info('No scanmap data currently present.')
        return 0

    last_update_sent = get_last_timestamp()
    if last_update_sent is not None:
        latest_logs = [log for log in logs if float(log['timestamp']) > last_update_sent]
        logging.info(f"{len(latest_logs)} new logs to send")
    else:
        logging.info('Timestamp for last log sent not found. Sending most recent log line only')
        latest_logs = [logs[-1]]
    if len(latest_logs) == 0:
        return 0

    last_timestamp = None
    for idx, log in enumerate(latest_logs):
        logging.info(f"Sending event from timestamp: {log['timestamp']}")
        ret = send_log_item(log)
        if ret is not None:
            last_timestamp = ret
        else:
            save_last_timestamp(last_timestamp)
            return idx
    save_last_timestamp(last_timestamp)

    return len(latest_logs)

# Tweet any log updates from scanmap since the last execution
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    if not DAEMON:
        logging.info('Running in oneshot mode.')
        ret = handle_log_batch()
        if ret < 0:
            exit(1)
        else:
            exit(0)
    else:
        logging.info(f"Running in daemon mode. Current update interval: {UPDATE_INTERVAL} seconds")
        while True:
            handle_log_batch()
            time.sleep(UPDATE_INTERVAL - ((time.time() - APP_STARTUP_TIME) % UPDATE_INTERVAL))

if __name__ == '__main__':
    main()
