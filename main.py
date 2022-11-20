import jsonpickle
from flask import Flask, request

import consts
import utils
from cluster import Cluster
from messaging import Message, start_sending_messages
from node import ClusterNode
from utils import *
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

node_id = int(utils.env("NODE_ID"))
consts.SERVER_PORT = int(utils.env("SERVER_PORT"))
cluster = Cluster(utils.env("IP_NETWORK"), int(utils.env("IP_OFFSET")), int(utils.env("NODES_COUNT")),
                  current_node=node_id)
node = ClusterNode(node_id, cluster)


@app.route("/health")
def health_check():
    return "<p>It works!</p>"


@app.route('/message', methods=['POST'])
def process_message():
    message = jsonpickle.decode(request.data, keys=True)
    node.handle_message(message)

    return "ok"


def start_server():
    app.run("0.0.0.0", consts.SERVER_PORT)


sending_thread = threading.Thread(target=start_sending_messages)
sending_thread.daemon = True
sending_thread.start()

server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

# node.start_election()

server_thread.join()
