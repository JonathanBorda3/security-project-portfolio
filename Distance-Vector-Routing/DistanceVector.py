# DistanceVector.py — Distributed Bellman-Ford routing algorithm
#
# Each node only knows about itself and its direct neighbors.
# Nodes exchange distance vectors with neighbors until the network converges
# on the shortest paths. Handles negative edge weights and negative cycles.

from Node import *
from helpers import *

NEGATIVE_INFINITY = -99


class DistanceVector(Node):

    def __init__(self, name, topolink, outgoing_links, incoming_links):
        super(DistanceVector, self).__init__(name, topolink, outgoing_links, incoming_links)

        # Distance vector: {destination_name: shortest_cost}
        # Start knowing myself at 0 and direct neighbors at their link weights
        self.distance_vector = {}
        self.distance_vector[self.name] = 0

        for link in self.outgoing_links:
            self.distance_vector[link.name] = int(link.weight)

        # Used to detect changes so we know when to stop sending updates
        self.prev_distance_vector = None

    def send_initial_messages(self):
        # Send my DV to all upstream neighbors (nodes that have a link pointing to me)
        # Message format: (sender_name, dv_copy)
        for neighbor_name in self.neighbor_names:
            self.send_msg((self.name, self.distance_vector.copy()), neighbor_name)

    def process_BF(self):
        # Snapshot current state to check for changes later
        self.prev_distance_vector = self.distance_vector.copy()

        for msg in self.messages:
            sender_name = msg[0]
            neighbor_dv = msg[1]

            # Only useful if I have an outgoing link to this sender (traffic flows through outgoing links)
            link_info = self.get_outgoing_neighbor_weight(sender_name)
            if link_info == "Node Not Found":
                continue

            link_weight = link_info[1]

            for dest, cost in neighbor_dv.items():
                # Don't update distance to myself
                if dest == self.name:
                    continue

                # -99 means negative infinity — propagate it as-is
                if cost == NEGATIVE_INFINITY:
                    new_cost = NEGATIVE_INFINITY
                else:
                    new_cost = link_weight + cost
                    if new_cost <= NEGATIVE_INFINITY:
                        new_cost = NEGATIVE_INFINITY

                # Update if new destination or cheaper path found
                if dest not in self.distance_vector or new_cost < self.distance_vector[dest]:
                    self.distance_vector[dest] = new_cost

        self.messages = []

        # Self-distance is always 0 (prevents negative self-cycles)
        self.distance_vector[self.name] = 0

        # Only re-advertise if something changed — this is how the algorithm terminates
        if self.distance_vector != self.prev_distance_vector:
            dv_to_send = self.distance_vector.copy()
            dv_to_send[self.name] = 0

            for neighbor_name in self.neighbor_names:
                self.send_msg((self.name, dv_to_send), neighbor_name)

    def log_distances(self):
        entries = []
        for dest, cost in self.distance_vector.items():
            entries.append("({},{})".format(dest, cost))

        log_string = " ".join(entries)
        add_entry(self.name, log_string)
