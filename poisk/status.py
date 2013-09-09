import requests
import json
import socket
import threading
import time
import datetime

STATUS_URL = "http://status.kreativitaet-trifft-technik.de/api/statusStream?spaceOpen=1&spaceDevices=1"

from poisk import app, db
from poisk.models import User

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('spaceticker')

def parsed_events(events):
    for event_lines in events:
        resp = {}
        for line in event_lines:
            key, value = line.split(': ', 1)
            try:
                resp[key] = json.loads(value)
            except ValueError:
                resp[key] = value
        yield resp

def event_chunks(resp):
    last_event_data = []
    for line in resp.iter_lines(1):
        if not line:
            if last_event_data:
                yield last_event_data
            last_event_data = []
        else:
            last_event_data.append(line)

class SpaceStatus(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        for evt in self.events():
            if evt.get('event') == 'spaceDevices':
                self.handle_spaceDevices(evt['data'])

    def handle_spaceDevices(self, evt):
        with app.test_request_context():
            for p in evt.get('people', []):
                user = User.query.filter_by(nick=p['id']).first()
                if user:
                    user.last_seen = datetime.datetime.utcnow()
            db.session.commit()

    def events(self):
        while True:
            try:
                resp = requests.get(STATUS_URL, stream=True, timeout=60*60)
                if resp.status_code != 200:
                    log.error('request error: %s' % resp)
                    time.sleep(60)
                for event in parsed_events(event_chunks(resp)):
                    yield event
            except socket.timeout:
                time.sleep(10)
                continue
            except requests.RequestException, ex:
                log.error('request error: %s' % ex)
                time.sleep(60)
            except Exception:
                log.exception('unknown request error:')
                time.sleep(60)

if __name__ == '__main__':
    def status_callback(open):
        if open:
            print "It's open!"
        else:
            print "It's closed!"
    s = SpaceStatus()
    s.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass
