import queue
from enum import Enum

import jsonpickle
import requests

from consts import SERVER_PORT
from utils import log

sending_queue = queue.Queue(maxsize=4096)


class MessageType(Enum):
    ELECTION = 1,
    ANSWER = 2,
    VICTORY = 3,
    COLOR = 4,
    PING = 5,
    PONG = 6,
    INFORM = 7


class Message:
    def __init__(self, type: MessageType, sender: int, data: str):
        self.type = type
        self.data = data
        self.sender = sender


def send_message(ip: str, message: Message):
    log("\tsending: ---> " + ip + ": type: " + str(message.type) + " (value: " + message.data + ")")
    sending_queue.put((ip, message))


def start_sending_messages():
    while True:
        try:
            (ip, message) = sending_queue.get(block=True)
            __send_message_internal(ip, message)
        except Exception as err:
            pass
            # log("error dequeue" + str(err))


def __send_message_internal(ip: str, message: Message):
    url = "http://" + ip + ":" + str(SERVER_PORT) + "/message"
    data = jsonpickle.encode(message, keys=True)

    # log("sending: " + ip + " ---> " + str(message.type) + " (" + message.data + ")")
    try:
        requests.post(url, data, timeout=0.3)
        # log("done: " + ip + " ---> " + str(message.type) + " (" + message.data + ")")
    except Exception as err:
        # log(url + ": " + str(err))
        pass
