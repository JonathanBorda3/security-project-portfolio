"""
Spanning Tree Protocol Implementation
Main switch class that implements the distributed STP algorithm
"""

from Message import *
from StpSwitch import *


class Switch(StpSwitch):

    def __init__(self, idNum, topolink, neighbors):
        # Initialize parent class
        super(Switch, self).__init__(idNum, topolink, neighbors)

        # Data structure to track spanning tree state
        self.root = self.switchID  # Current known root (starts as self)
        self.distance = 0  # Hops to root
        self.active_links = dict.fromkeys(neighbors, True)  # Active tree links
        self.switch_through = self.switchID  # Neighbor on path to root


    def process_message(self, message):
        """
        Main STP algorithm - processes incoming messages from neighbors
        and updates spanning tree state accordingly
        """
        
        # Case 1: Discovered a better (lower ID) root
        if message.root < self.root:
            self.root = message.root
            self.distance = message.distance + 1
            self.active_links[message.origin] = True
            self.switch_through = message.origin
            self.helper(message.ttl)

        # Case 2: Message about current root
        elif message.root == self.root:
            
            # Sender is farther from root than us
            if message.distance + 1 > self.distance:
                if message.pathThrough is True:
                    # They go through us - keep link and propagate
                    self.active_links[message.origin] = True
                    self.helper(message.ttl)
                else:
                    # They don't need us
                    self.active_links[message.origin] = False
                return
            
            # Sender has shorter path to root
            if message.distance + 1 < self.distance:
                self.distance = message.distance + 1
                self.active_links[message.origin] = True
                self.switch_through = message.origin
                self.helper(message.ttl)
                
            # Same distance - need tie breaker
            elif message.distance + 1 == self.distance:
                
                # Switch to lower ID neighbor
                if message.origin < self.switch_through:
                    self.active_links[self.switch_through] = False
                    self.active_links[message.origin] = True
                    self.switch_through = message.origin
                    self.helper(message.ttl)
                
                # Keep current higher ID neighbor
                elif message.origin > self.switch_through:
                    self.active_links[message.origin] = False
                    self.helper(message.ttl)
                
                # Message from current parent
                else:
                    self.active_links[message.origin] = True
                    self.helper(message.ttl)
        
        # Case 3: Sender has outdated root info
        else:
            # Check pathThrough even with wrong root
            if message.pathThrough:
                self.active_links[message.origin] = True
            else:
                self.active_links[message.origin] = False
            # Send correction
            self.helper(message.ttl)

                    
    def helper(self, ttl):
        """
        Sends messages to all neighbors with updated spanning tree info.
        Decrements TTL to enable topology change detection.
        """
        new_ttl = ttl - 1
        
        # Continue sending until TTL expires (>= 0 allows TTL=0 messages)
        if new_ttl >= 0:
            for neighbour in self.links:
                # Determine if this neighbor is on our path to root
                this_path_through = False
                if neighbour == self.switch_through:
                    this_path_through = True
                
                # Create and send message
                msg = Message(self.root, self.distance,
                                self.switchID, neighbour, this_path_through, new_ttl)
                self.send_message(msg)


    def generate_logstring(self):
        """
        Generates output string showing active links in the spanning tree
        Format: "switchID - neighborID, switchID - neighborID, ..."
        """
        to_return = ""
        sorted_links = sorted(self.active_links.items())
        
        for key, value in sorted_links:
            if value is True:
                to_return += "%d - %d, " % (self.switchID, key)
        
        # Remove trailing comma and space
        to_return = to_return[:-2]
        return to_return
