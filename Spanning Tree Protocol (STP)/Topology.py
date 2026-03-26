"""
Topology - Network topology manager
Handles switch creation, message queuing, and topology changes
"""

from Message import *
from Switch import Switch


class Topology(object):

    def __init__(self, conf_file: str):
        """This creates all the switches in the Topology from the configuration
        file passed into __init__(). May throw an exception if there is a
        problem with the config file.
        """
        self.switches = {}
        self.messages = []
        self.dropped_switches = []
        self.ttl_limit = 5 # default
        self.drops = [] # default
        self.drop_complete = False
        self.conf_topo = {}
        self.import_conf(conf_file)

    def import_conf(self, conf_file: str):
        try:
            conf = __import__(conf_file)
            if hasattr(conf, "ttl_limit"):
                self.ttl_limit = conf.ttl_limit
            if hasattr(conf, "drops"):
                self.drops = conf.drops
                self.conf_topo = conf.topo
            for key in list(conf.topo.keys()):
                self.switches[key] = Switch(key, self, conf.topo[key])
            # Verify the topology read from file was correct.
            for key in list(self.switches.keys()):
                self.switches[key].verify_neighbors()
        except Exception:
            print(f"Error importing conf_file: {conf_file}")
            raise

    def send_message(self, message: Message):
        if not message.verify_message():
            print("Message is not properly formatted")
            return
        if message.destination in self.switches[message.origin].links:
            self.messages.append(message)
        elif message.origin in self.dropped_switches or message.destination in self.dropped_switches:
            pass
        else:
            print("Messages can only be sent to immediate neighbors")

    def restart_topology_messages(self):
        self.messages = []
        for switch in self.switches:
            self.switches[switch].send_initial_messages()

    def run_spanning_tree(self):
        """This function drives the simulation of a Spanning Tree. It first sends the initial
        messages from each node by invoking send_intial_message. Afterward, each message
        is delivered to the destination switch, where process_message is invoked.
        """
        self.restart_topology_messages()

        while len(self.messages) > 0:
            msg = self.messages.pop(0)
            self.switches[msg.destination].process_message(msg)
            if msg.ttl == 0 and not self.drop_complete:
                for switchId in self.drops:
                    self.drop_switch(switchId)
                self.drop_complete = True

    def drop_switch(self, switchId):
        if switchId not in self.dropped_switches:
            for key in self.switches:
                if switchId in self.conf_topo[key]:
                    self.conf_topo[key].remove(switchId)
                self.switches[key] = Switch(key, self, self.conf_topo[key])
            del self.switches[switchId]
            self.dropped_switches.append(switchId)
            self.restart_topology_messages()

    def log_spanning_tree(self, filename: str):
        """This function drives the logging of the text file representing the spanning tree.
        It is invoked at the end of the simulation, and iterates through the switches in
        increasing order of ID and invokes the generate_logstring function.  That string
        is written to the file as provided by the student code.
        """
        with open(filename, 'w') as out:
            for switch in sorted(self.switches.keys()):
                entry = self.switches[switch].generate_logstring()
                if switch not in self.dropped_switches:
                    entry += "\n"
                out.write(entry)
            out.close()
