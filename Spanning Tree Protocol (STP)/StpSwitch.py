"""
StpSwitch - Parent class for Switch implementation
Provides helper methods for message passing and topology verification
"""

from Message import *


class StpSwitch(object):

    def __init__(self, idNum: int, topolink: object, neighbors: list):
        """
        switchID: int
            the ID of the switch (lowest value determines root and breaks ties)
        topology: Topology object
            a backlink to the Topology class.
            Used for sending messages: self.topology.send_message(message)
        links: list
            the list of switch IDs connected to this switch object
        """
        self.switchID = idNum
        self.topology = topolink
        self.links = neighbors

    # Invoked at initialization of topology of switches, this does NOT need to be invoked by student code.
    # Do NOT overwrite this function in Switch.py
    def verify_neighbors(self):
        """ Verify that all your neighbors have a backlink to you. """
        for neighbor in self.links:
            if self.switchID not in self.topology.switches[neighbor].links:
                raise Exception(f"{str(neighbor)} does not have link to {str(self.switchID)}")

    # Invoked at initialization of topology of switches, this does NOT need to be invoked by student code.
    # Do NOT overwrite this function in Switch.py
    def send_initial_messages(self):
        """ Sends all the initial messages.
                Called in Topology.run_spanning_tree()
        """
        for destinationID in self.links:
            self.send_message(
                Message(self.switchID, 0, self.switchID, destinationID, False, self.topology.ttl_limit)
            )

    # Wrapper for message passing to allow students from avoid using self.topology directly
    # Do NOT overwrite this function in Switch.py
    def send_message(self, message: Message):
        self.topology.send_message(message)

    def __str__(self):
        return (f"""Switch<switchID: {self.switchID}, links: {self.links}>""")
