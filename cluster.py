import math
from typing import List, Optional

from consts import *
from messaging import send_message, Message, MessageType
from utils import create_timeout, log


class Cluster:
    def __init__(self, ip_network: str, ip_offset: int, nodes_count: int, current_node: int):
        self.ip_network = ip_network
        self.ip_offset = ip_offset
        self.nodes_count = nodes_count
        self.current_node = current_node

        self.leader = None

        self.ips = [self.ip_network + "." + str(self.ip_offset + i) for i in range(self.nodes_count)]
        self.colors: List[Optional[str]] = [None for i in range(self.nodes_count)]
        self.alive = [False for i in range(self.nodes_count)]

        self.color_nodes_timer = None

    def get_higher_ids(self, higher_than) -> List[int]:
        return [i for i in range(higher_than + 1, self.nodes_count)]

    def get_lower_ids(self, lower_than) -> List[int]:
        return [i for i in range(0, lower_than)]

    def convert_to_ips(self, ids: List[int]):
        return [self.ips[i] for i in ids]

    def leader_changed(self, new_leader):
        self.leader = new_leader
        if self.leader == self.current_node:
            self.check_alive()
            self.color_nodes_timer = create_timeout(ALIVE_TIMEOUT, self.color_nodes)  # check for check alive to finish

    def check_alive(self):
        for i in range(self.nodes_count):
            self.alive[i] = False
            send_message(self.ips[i], Message(MessageType.PING, self.current_node, ""))

    def pong_received(self, node_id):
        self.alive[node_id] = True

    def color_nodes(self):
        if self.leader is None:
            return

        self.__determine_coloring()

        for i in range(self.nodes_count):
            send_message(self.ips[i], Message(MessageType.COLOR, self.current_node, self.colors[i]))

    def __determine_coloring(self):
        total_live = self.alive.count(True)
        log("alive: " + str(self.alive) + " (count: " + str(total_live) + ")")

        green_nodes_left = math.ceil(total_live * GREEN_COLOR_REQUIRED)

        self.colors[self.leader] = "GREEN"  # leader always green
        green_nodes_left -= 1

        for i in range(self.nodes_count):
            if i == self.leader:
                continue

            if self.alive[i]:
                if i < green_nodes_left:
                    self.colors[i] = "GREEN"
                    green_nodes_left -= 1
                else:
                    self.colors[i] = "RED"
            else:
                self.colors[i] = "-"

        log("new colors assigned: " + str(self.colors))
