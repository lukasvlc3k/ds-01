from datetime import datetime
from typing import List, Optional

from cluster import Cluster
from consts import *
from messaging import Message, send_message, MessageType
from utils import *


class ClusterNode:
    def __init__(self, node_id: int, cluster: Cluster):
        self.node_id = node_id
        self.cluster = cluster
        self.color = None

        self.call_me_leader_timeout: Optional[threading.Timer] = None
        self.election_reset_timeout: Optional[threading.Timer] = None
        self.election_in_progress = False

        self.ping_leader_timer: threading.Timer = create_timeout(PING_INTERVAL, self.ping_leader)
        self.ping_leader_timeout: Optional[threading.Timer] = None

        self.inform_timer: threading.Timer = create_timeout(INFORM_INTERVAL, self.inform)
        self.check_leader_timer: threading.Timer = create_timeout(CHECK_LEADER_INTERVAL, self.check_leader)

        log("init")
        self.log_current_state()

    def get_higher_ids(self) -> List[int]:
        return self.cluster.get_higher_ids(self.node_id)

    def get_lower_ids(self) -> List[int]:
        return self.cluster.get_lower_ids(self.node_id)

    def send_to_all(self, message: Message):
        for ip in self.cluster.ips:
            send_message(ip, message)

    def send_to_higher(self, message: Message):
        for ip in self.cluster.convert_to_ips(self.get_higher_ids()):
            send_message(ip, message)

    def send_to_lower(self, message: Message):
        for ip in self.cluster.convert_to_ips(self.get_lower_ids()):
            send_message(ip, message)

    def create_message(self, type: MessageType, data: str):
        return Message(type, self.node_id, data)

    def ping_leader(self):
        if self.cluster.leader is not None:
            send_message(self.cluster.ips[self.cluster.leader], Message(MessageType.PING, self.node_id, "ping"))
            self.ping_leader_timeout = create_timeout(LEADER_PING_TIMEOUT, self.leader_timeout)

        self.ping_leader_timer = create_timeout(PING_INTERVAL, self.ping_leader)

    def leader_timeout(self):
        log("LEADE LOST...")
        self.start_election()

    def inform(self):
        self.inform_timer = create_timeout(INFORM_INTERVAL, self.inform)

        if self.cluster.leader is not None:
            msg: Message = Message(MessageType.INFORM, self.node_id, str(self.cluster.leader))
            self.send_to_all(msg)

    def check_leader(self):
        self.check_leader_timer = create_timeout(CHECK_LEADER_INTERVAL, self.check_leader)

        if self.cluster.leader is None:
            log("NO LEADER FOUND")
            self.start_election()

    def cancel_leader_timeout(self):
        if self.ping_leader_timeout is not None:
            self.ping_leader_timeout.cancel()

    def call_me_leader(self):
        self.send_to_lower(self.create_message(MessageType.VICTORY, str(self.node_id)))
        self.cluster.leader_changed(self.node_id)

        log("I WAS SELECTED AS A LEADER")
        self.log_current_state()
        self.election_in_progress = False

    def start_election(self):
        log("no leader, election started")
        self.log_current_state()

        self.election_in_progress = True

        self.send_to_higher(self.create_message(MessageType.ELECTION, str(self.node_id)))
        self.call_me_leader_timeout = create_timeout(CALL_ME_LEADER_TIMEOUT, self.call_me_leader)

        return
        # if self.node_id == self.cluster.nodes_count - 1:
        #    # current node has the highest ID
        #    self.call_me_leader()
        # else:
        #    self.send_to_higher(self.create_message(MessageType.ELECTION, str(self.node_id)))
        #    self.call_me_leader_timeout = create_timeout(CALL_ME_LEADER_TIMEOUT, self.call_me_leader)

    def cancel_call_me_leader_timer(self):
        if self.call_me_leader_timeout is not None:
            self.call_me_leader_timeout.cancel()

    def cancel_election_reset_timer(self):
        if self.election_reset_timeout is not None:
            self.election_reset_timeout.cancel()

    def log_current_state(self):
        log("- current state: color: " + str(self.color) + ", leader: " + str(self.cluster.leader))

    def handle_message(self, message: Message):
        # log("\thandling message: sender: " + str(message.sender) + ", type: " + str(
        #     message.type) + ", value: " + message.data)

        if message.type == MessageType.ANSWER:
            if message.sender > self.node_id:
                self.cancel_call_me_leader_timer()
                self.cancel_election_reset_timer()
                self.election_reset_timeout = create_timeout(ELECTION_RESET_TIMEOUT, self.start_election)

                log("I won't be leader, there is a node with higher id...")
                self.log_current_state()

        if message.type == MessageType.ELECTION:
            if message.sender < self.node_id:
                send_message(self.cluster.ips[message.sender], self.create_message(MessageType.ANSWER, ""))

                self.cancel_call_me_leader_timer()
                self.cancel_election_reset_timer()
                log("someone with lower id tries to be leader. Prevented.")
                self.log_current_state()

                if not self.election_in_progress:
                    self.start_election()

        if message.type == MessageType.VICTORY:
            self.cluster.leader_changed(message.sender)
            self.election_in_progress = False
            self.cancel_call_me_leader_timer()
            self.cancel_election_reset_timer()

            log("new leader won the election: " + str(message.sender))
            self.log_current_state()

        if message.type == MessageType.COLOR:
            if message.sender == self.cluster.leader:
                self.color = message.data
                log("new color assigned: " + self.color)
                self.log_current_state()

                self.log_current_state()
                self.election_in_progress = False

        if message.type == MessageType.PING:
            send_message(self.cluster.ips[message.sender], Message(MessageType.PONG, self.node_id, ""))

        if message.type == MessageType.PONG:
            if message.sender == self.cluster.leader:
                # log("PONG received from leader")
                self.cancel_leader_timeout()

            self.cluster.pong_received(message.sender)

        if message.type == MessageType.INFORM:
            leader_received = int(message.data)
            if self.cluster.leader is None:
                self.cluster.leader_changed(leader_received)
                log("leader set from INFORM message")
                self.log_current_state()

            if self.cluster.leader != leader_received:
                log("Leader mismatch - received: " + str(leader_received) + ", current: " + str(self.cluster.leader))
                self.log_current_state()

                self.start_election()
