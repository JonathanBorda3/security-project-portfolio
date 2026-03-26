"""
Message class for Spanning Tree Protocol
Defines message format for switch-to-switch communication
"""


class Message(object):

    def __init__(self, claimedRoot: int, distanceToRoot: int, originID: int, destinationID: int, pathThrough: bool, ttl: int = 5):
        """
        root: int
            the ID of the switch thought to be the root by the origin switch
        distance: int
            the distance of the origin to the root
        origin: int
            the ID of the origin switch (sender)
        destination: int
            the ID of the destination switch (receiver)
        pathThrough: bool
            indicating the path to the claimed root from the origin passes through the destination
        ttl: int
            the time to live remaining on this message
        """
        self.root = claimedRoot
        self.distance = distanceToRoot
        self.origin = originID
        self.destination = destinationID
        self.pathThrough = pathThrough
        self.ttl = ttl

    def verify_message(self):
        """
        Member function that returns True if the message is properly formed, and False otherwise
        """
        valid = True

        if self.pathThrough != True and self.pathThrough != False:
            valid = False
        if isinstance(self.root, int) is False or isinstance(self.distance, int) is False or \
                isinstance(self.origin, int) is False or isinstance(self.destination, int) is False or \
                    isinstance(self.ttl, int) is False:
            valid = False

        return valid

    def __str__(self):
        return (f"""Message<root: {self.root}, distance: {self.distance}, origin: {self.origin}, destination: {self.destination}, pathThrough: {self.pathThrough}, ttl: {self.ttl}>""")
