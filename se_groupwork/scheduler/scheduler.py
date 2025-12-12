#!/usr/bin/env python3
"""
Simple scheduler that runs two management commands every day at 00:00 and 12:00
in the specified timezone. It calls Django management commands in sequence:
  1) webspider's `update_public_accounts`
  2) remoteAI's `process_articles`

Configure timezone with environment variable `SCHEDULER_TZ` (default: Asia/Shanghai).
"""
import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta, time as dtime

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(asctime)s] %(message)s')

TZ_NAME = os.getenv('SCHEDULER_TZ', 'Asia/Shanghai')
try:
    tz = ZoneInfo(TZ_NAME) if ZoneInfo is not None else None
except Exception:
    logging.warning('ZoneInfo not available or invalid TZ=%s, falling back to system local time', TZ_NAME)
    tz = None

COMMANDS = [
    [sys.executable, 'manage.py', 'update_public_accounts'],
    [sys.executable, 'manage.py', 'process_articles'],
]


def now(tzinfo=None):
    if tzinfo:
        return datetime.now(tz=tzinfo)
    return datetime.now()


def next_run_after(dt, tzinfo=None):
    # Candidate times: today 00:00, today 12:00, tomorrow 00:00, tomorrow 12:00
    if tzinfo:
        today = dt.date()
    else:
        today = dt.date()
    candidates = []
    for add_day in (0, 1):
        d = today + timedelta(days=add_day)
        for hh in (0, 12):
            candidate = datetime.combine(d, dtime(hh, 0, 0))
            if tzinfo:
                candidate = candidate.replace(tzinfo=tzinfo)
            candidates.append(candidate)
    # pick smallest candidate > dt
    future = [c for c in candidates if c > dt]
    if not future:
        # fallback: schedule 12 hours later
        return dt + timedelta(hours=12)
    return min(future)


def run_commands():
    for cmd in COMMANDS:
        logging.info('Running command: %s', ' '.join(cmd))
        try:
            completed = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            logging.info('Command finished: %s (exit=%s)\n%s', ' '.join(cmd), completed.returncode, completed.stdout)
        except Exception as e:
            logging.exception('Exception while running %s: %s', ' '.join(cmd), e)


def main():
    logging.info('Scheduler starting (TZ=%s)', TZ_NAME)
    while True:
        current = now(tz)
        nr = next_run_after(current, tz)
        delta = (nr - current).total_seconds()
        logging.info('Next run scheduled at %s (in %s seconds)', nr.isoformat(), int(delta))
        # sleep in small chunks so signals can be handled
        slept = 0
        while slept < delta:
            to_sleep = min(60, delta - slept)
            time.sleep(to_sleep)
            slept += to_sleep
        # time to run
        logging.info('Starting scheduled tasks')
        run_commands()
        logging.info('Scheduled tasks completed')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info('Scheduler interrupted, exiting')
        sys.exit(0)
