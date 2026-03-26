#!/usr/bin/python
# SDN Firewall Implementation with POX

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.revent import *
from pox.lib.addresses import EthAddr


def firewall_policy_processing(policies):
    """
    Reads firewall rules from configure.pol and builds OpenFlow flow modification
    objects for each one. Each policy is a dictionary with keys like 'mac-src',
    'ip-dst', 'ipprotocol', 'port-dst', 'action', etc. A dash '-' means that
    field isn't used for matching.

    Returns a list of flow_mod objects that get sent to the OpenFlow switch.
    """

    rules = []

    for policy in policies:

        rule = of.ofp_flow_mod()
        rule.match = of.ofp_match()

        # figure out if we need to set dl_type = IPv4
        # this is required as a prerequisite whenever we match on any IP-level field
        need_ip = (policy['ip-src'] != '-' or policy['ip-dst'] != '-' or
                   policy['ipprotocol'] != '-' or policy['port-src'] != '-' or
                   policy['port-dst'] != '-')

        if need_ip:
            rule.match.dl_type = 0x800

        # match on MAC addresses if specified
        if policy['mac-src'] != '-':
            rule.match.dl_src = EthAddr(policy['mac-src'])

        if policy['mac-dst'] != '-':
            rule.match.dl_dst = EthAddr(policy['mac-dst'])

        # match on IP addresses - pass the CIDR string directly to POX
        if policy['ip-src'] != '-':
            rule.match.nw_src = policy['ip-src']

        if policy['ip-dst'] != '-':
            rule.match.nw_dst = policy['ip-dst']

        # match on IP protocol (1=ICMP, 6=TCP, 17=UDP)
        if policy['ipprotocol'] != '-':
            rule.match.nw_proto = int(policy['ipprotocol'])

        # match on TCP/UDP ports
        if policy['port-src'] != '-':
            rule.match.tp_src = int(policy['port-src'])

        if policy['port-dst'] != '-':
            rule.match.tp_dst = int(policy['port-dst'])

        # allow rules get higher priority so they override block rules
        if policy['action'] == 'Allow':
            rule.priority = 5000
            rule.actions.append(of.ofp_action_output(port=of.OFPP_NORMAL))
        else:
            rule.priority = 1000
            # no action means the packet just gets dropped

        print('Added Rule ',policy['rulenum'],': ',policy['comment'])
        rules.append(rule)

    return rules
