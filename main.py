import requests
from datetime import datetime

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


# Reads (from file) the timestamp of the last log item sent
# Returns None if not found
def get_last_timestamp():
    last_update_sent = None

    try:
        with open(LAST_UPDATE_FILENAME, 'r') as f:
            last_update_sent = float(f.read())
    except FileNotFoundError:
        pass
    except Exception as e:
        # Treat any kind of error as if we haven't sent updates before
        print(e)

    return last_update_sent


# Write the given timestamp to a file for reading on the next execution
def save_last_timestamp(timestamp):
    print(f'Updating last update file with timestamp {timestamp}')
    with open(LAST_UPDATE_FILENAME, 'w') as f:
        f.write(timestamp)


# Render a log item to a formatted string for Telegram
def format_message(data, timestamp):
    emoji = LABELS.get(data['label'], '')
    label = data['label'].replace('_', ' ').capitalize() if data['label'] != 'other' else ''
    time = datetime.fromtimestamp(float(timestamp)).strftime('%I:%M%p\n%m/%d/%Y')

    return f"{emoji + ' ' if emoji else ''}{label + ' at ' if label else ''}{data['location']}\n{data['text']}\n\n{time}\nvia <a href='{SITE_URL}'>{SITE_NAME}</a>"


# Send a log item via Telegram bot and return the timestamp
def send_log_item(log):
    message = format_message(log['data'], log['timestamp'])
    params = {"chat_id": TELEGRAM_CHAT, "text": message, "disable_web_page_preview": True, "parse_mode": "HTML"}
    requests.request("GET", f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params=params)

    return log['timestamp']


# Tweet any log updates from scanmap since the last execution
def main():
    response = requests.get(config.LOG_URL)
    parsed_response = response.json()
    logs = parsed_response['logs']

    last_update_sent = get_last_timestamp()
    if last_update_sent:
        latest_logs = [log for log in logs if float(log['timestamp']) > last_update_sent]
        print(f"{len(latest_logs)} new logs to send")
    else:
        print('Timestamp for last log sent not found. Sending most recent log line only')
        latest_logs = [logs[-1]]

    if len(latest_logs) == 0:
        exit(0)

    last_timestamp = None
    for log in latest_logs:
        try:
            last_timestamp = send_log_item(log)
            print(last_timestamp)
        except:
            print('Unexpected error.')
            break

    if last_timestamp:
        save_last_timestamp(last_timestamp)

if __name__ == '__main__':
    main()