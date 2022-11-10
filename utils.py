import os
import threading
from datetime import datetime


def env(key: str):
    return os.getenv(key)


def create_timeout(timeout, callback) -> threading.Timer:
    timeout_timer = threading.Timer(timeout, callback)
    timeout_timer.start()
    return timeout_timer


def log(message):
    print(f'[{datetime.utcnow()}]: \t{message}', flush=True)
