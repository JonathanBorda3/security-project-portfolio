"""
Spanning Tree Protocol Implementation - Annotated Version
This version includes detailed comments explaining the algorithm
"""

from Message import *
from StpSwitch import *


class Switch(StpSwitch):

    def __init__(self, idNum, topolink, neighbors):
        # Call the parent class constructor to set up basic switch stuff
        super(Switch, self).__init__(idNum, topolink, neighbors)

        # Data structure to keep track of the spanning tree
        # Each switch starts thinking it's the root
        self.root = self.switchID
        self.distance = 0  # distance to root (0 since we think we're the root)
        # Start with all links active (we'll figure out which ones to keep later)
        self.active_links = dict.fromkeys(neighbors, True)
        # This tracks which neighbor we go through to reach the root
        self.switch_through = self.switchID



    def process_message(self, message):
        """
        This is where the main STP algorithm happens. We process incoming messages
        and decide how to update our view of the spanning tree.
        """
        
        # CASE 1: Someone told us about a better (lower ID) root than we currently know
        if message.root < self.root:
            # Update to the new better root
            self.root = message.root
            self.distance = message.distance + 1  # our distance is their distance + 1
            self.active_links[message.origin] = True  # activate link to whoever told us
            self.switch_through = message.origin  # we now go through them to reach root
            # Send updates to all our neighbors about this new root
            self.helper(message.ttl)

        # CASE 2: Message is about the same root we already know
        elif message.root == self.root:
            
            # CASE 2a: Message is from someone farther from the root than us
            if message.distance + 1 > self.distance:
                # Check if they're trying to go through us to reach the root
                if message.pathThrough is True:
                    self.active_links[message.origin] = True  # keep link active
                    # Need to propagate this info so our other neighbors know
                    self.helper(message.ttl)
                else:
                    # They have a different path, don't need this link
                    self.active_links[message.origin] = False
                # Either way, don't process further since they're farther away
                return
            
            # CASE 2b: Message shows a shorter path to root than we currently have
            if message.distance + 1 < self.distance:
                # Update our distance and path
                self.distance = message.distance + 1
                self.active_links[message.origin] = True
                self.switch_through = message.origin
                # Tell everyone about this better path
                self.helper(message.ttl)
                
            # CASE 2c: Same distance - need to break the tie
            elif message.distance + 1 == self.distance:
                
                # If the new path is through a lower ID neighbor, switch to it
                if message.origin < self.switch_through:
                    self.active_links[self.switch_through] = False  # disable old path
                    self.active_links[message.origin] = True  # enable new path
                    self.switch_through = message.origin
                    self.helper(message.ttl)
                
                # If it's through a higher ID neighbor, stick with current path
                elif message.origin > self.switch_through:
                    self.active_links[message.origin] = False
                    # Still need to propagate since link status changed
                    self.helper(message.ttl)
                
                # Message is from our current parent
                else:  # message.origin == self.switch_through
                    # Always keep the link to our parent active
                    self.active_links[message.origin] = True
                    # Keep propagating messages to maintain TTL countdown
                    self.helper(message.ttl)
        
        # CASE 3: Message has a worse (higher ID) root - they have outdated info
        else:  # message.root > self.root
            # Still check pathThrough since they might be our child with old info
            if message.pathThrough:
                self.active_links[message.origin] = True
            else:
                self.active_links[message.origin] = False
            # Send them a correction about the actual root
            self.helper(message.ttl)
                    
    def helper(self, ttl):
        """
        Helper function to send messages to all our neighbors.
        This decrements TTL and only sends if TTL hasn't expired.
        """
        new_ttl = ttl - 1  # decrement the time-to-live
        
        # Only send messages if TTL hasn't expired (>= 0 allows TTL=0 messages)
        if new_ttl >= 0:
            # Send a message to each neighbor
            for neighbour in self.links:
                # Figure out if this neighbor is on our path to root
                this_path_through = False
                if neighbour == self.switch_through:
                    this_path_through = True
                
                # Create and send the message with all the required info
                msg = Message(self.root, self.distance,
                                self.switchID, neighbour, this_path_through, new_ttl)
                self.send_message(msg)

    def generate_logstring(self):
        """
        Creates the output string showing which links are active.
        Format: "switchID - neighborID, switchID - neighborID, ..."
        """
        to_return = ""
        # Sort the links to make output consistent
        sorted_links = sorted(self.active_links.items())
        
        # Add each active link to the output string
        for key, value in sorted_links:
            if value is True:
                to_return += "%d - %d, " % (self.switchID, key)
        
        # Remove the trailing comma and space
        to_return = to_return[:-2]
        return to_return
