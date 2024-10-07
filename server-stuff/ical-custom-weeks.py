"""
Author: phil (cemiu)

iCal url for custom week numbers
hosted on https://cemiu.net/tools/weeknum.ics?start=...

Subscript to URL, passing a monday (!) as param, e.g.:
https://cemiu.net/tools/weeknum.ics?start=2024-09-30

It will populate your calendar with week numbers, with the passed date as the first week.

My use: Showing current week of academic year.
"""

from flask import Flask, request, Response
from flask_caching import Cache
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event

app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# YYYYMMDD or YYYY-MM-DD
DATE_REGEX = re.compile(r'^\d{4}-?\d{2}-?\d{2}$')

def create_error_calendar(error_message):
    """
    Creates a minimal iCalendar object with a single event describing the error.
    """
    cal = Calendar()
    cal.add('prodid', '-//Week Number Calendar//cemiu.net//')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', 'Error')
    event.add('description', error_message)
    event.add('dtstart', datetime.now())
    event.add('dtend', datetime.now() + timedelta(hours=1))
    event.add('dtstamp', datetime.now())
    event['uid'] = f'error-{datetime.now().timestamp()}@cemiu.net'
    cal.add_component(event)

    return cal

@cache.cached(timeout=60*60, query_string=True)  # Cache for 1 hour based on query string
@app.route('/tools/weeknum.ics')
def weeknum():
    start_str = request.args.get('start', '').replace('-', '')

    if DATE_REGEX.match(start_str):
        try:
            start_date = datetime.strptime(start_str, '%Y%m%d').date()
        except ValueError:
            error_cal = create_error_calendar("Error: Invalid date.")
            return Response(error_cal.to_ical(), mimetype='text/calendar'), 400
    else:
        error_cal = create_error_calendar("Error: .../tools/weeknum.ics?start=YYYY-MM-DD")
        return Response(error_cal.to_ical(), mimetype='text/calendar'), 400

    if start_date.weekday() != 0:
        error_cal = create_error_calendar("Error: The start date must be a Monday.")
        return Response(error_cal.to_ical(), mimetype='text/calendar'), 400

    cal = Calendar()
    cal.add('prodid', '-//Week Number Calendar//cemiu.net//')
    cal.add('version', '2.0')

    for i in range(52):
        event_date = start_date + timedelta(weeks=i)
        event = Event()
        event.add('summary', f'Week {i+1}')
        event.add('dtstart', event_date)
        event.add('dtend', event_date + timedelta(days=1))  # all-day event
        event.add('dtstamp', datetime.now())
        event['uid'] = f'week-{i+1}-{event_date.isoformat()}@cemiu.net'
        event.add('transp', 'TRANSPARENT')  # all-day event
        cal.add_component(event)

    return Response(cal.to_ical(), mimetype='text/calendar')

if __name__ == '__main__':
    app.run()

