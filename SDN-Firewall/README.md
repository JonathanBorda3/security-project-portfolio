# SDN Firewall with POX

## What This Project Is

This was a project for CS 6250 (Computer Networks) at Georgia Tech where I built a firewall for a simulated corporate network using Software Defined Networking. The idea is that instead of configuring each switch individually, you have one central controller (POX) that tells all the switches what to do with traffic — what to let through and what to drop.

The network simulates a company with 5 offices (Headquarters, US, India, China, UK) all connected through one switch, plus some external "world" hosts representing the internet.

| Network | Hosts | Subnet |
|---------|-------|--------|
| Headquarters | hq1–hq5 | 10.0.0.0/24 |
| US Office | us1–us5 | 10.0.1.0/24 |
| India Office | in1–in5 | 10.0.20.0/24 |
| China Office | cn1–cn5 | 10.0.30.0/24 |
| UK Office | uk1–uk5 | 10.0.40.0/24 |
| External | other1–other2 | 10.0.200.0/24 |

## What I Built

There were two main parts to code, plus a Wireshark packet capture.

### The Firewall Engine (sdn-firewall.py)

This is the Python code that reads a config file full of firewall rules and turns each one into an OpenFlow flow modification object that POX can understand. It needs to handle matching on MAC addresses, IP addresses (with CIDR notation), protocols like ICMP/TCP/UDP, and port numbers.

The tricky part was getting the priorities right — Allow rules need to override Block rules when they overlap, so I set Allow at priority 5000 and Block at 1000. I also had to make sure the OpenFlow prerequisites were set correctly (you can't match on a TCP port without first declaring you're matching IPv4 and TCP, or POX just silently ignores your rule).

```python
def firewall_policy_processing(policies):
    rules = []

    for policy in policies:
        rule = of.ofp_flow_mod()
        rule.match = of.ofp_match()

        # figure out if any IP-level field is being used — if so we need to declare IPv4
        need_ip = (policy['ip-src'] != '-' or policy['ip-dst'] != '-' or
                   policy['ipprotocol'] != '-' or policy['port-src'] != '-' or
                   policy['port-dst'] != '-')

        if need_ip:
            rule.match.dl_type = 0x800  # IPv4

        if policy['mac-src'] != '-':
            rule.match.dl_src = EthAddr(policy['mac-src'])

        if policy['mac-dst'] != '-':
            rule.match.dl_dst = EthAddr(policy['mac-dst'])

        if policy['ip-src'] != '-':
            rule.match.nw_src = policy['ip-src']

        if policy['ip-dst'] != '-':
            rule.match.nw_dst = policy['ip-dst']

        if policy['ipprotocol'] != '-':
            rule.match.nw_proto = int(policy['ipprotocol'])

        if policy['port-src'] != '-':
            rule.match.tp_src = int(policy['port-src'])

        if policy['port-dst'] != '-':
            rule.match.tp_dst = int(policy['port-dst'])

        # Allow gets higher priority so it overrides Block
        if policy['action'] == 'Allow':
            rule.priority = 5000
            rule.actions.append(of.ofp_action_output(port=of.OFPP_NORMAL))
        else:
            rule.priority = 1000
            # no action = packet gets dropped

        rules.append(rule)

    return rules
```

### The Firewall Rules (configure.pol)

I wrote 23 rules covering 7 different security scenarios:

- **Quarantine a host with a TCP worm** — block all outbound TCP from the infected machine
- **Fully isolate a compromised host** — block everything in both directions
- **ICMP ping access control** — block pings to certain subnets from the outside world, but allow HQ to still ping those subnets (this one was the trickiest because you need Allow overrides for HQ)
- **Block web server responses** — block a server from responding on ports 80/443 by filtering on source port, which also kills incoming connections since the server can never complete the TCP handshake
- **Restrict access to a microservice** — use CIDR notation (/28, /30) to target specific groups of hosts with minimal rules
- **Block a rogue device by MAC address** — catch a cloned device at Layer 2 regardless of what IP it's using
- **Block external SMTP access** — prevent the outside world from reaching port 25 on any corporate subnet

```
# Example rules (came with the project):
1,Block,-,-,10.0.0.1/32,10.0.1.0/24,6,-,80,Block 10.0.0.1 from accessing a web server on the 10.0.1.0/24 network
2,Allow,-,-,10.0.0.1/32,10.0.1.125/32,6,-,80,Allow 10.0.0.1 to access a web server on 10.0.1.125 overriding previous rule

# Task 1: Block cn4 TCP outbound (worm virus)
3,Block,-,-,10.0.30.4/32,-,6,-,-,Task 1 - Block cn4 from initiating TCP connections

# Task 2: Completely isolate cn5
4,Block,-,-,10.0.30.5/32,-,-,-,-,Task 2 - Block all traffic FROM cn5
5,Block,-,-,-,10.0.30.5/32,-,-,-,Task 2 - Block all traffic TO cn5

# Task 3: ICMP ping rules
6,Block,-,-,-,10.0.1.0/24,1,-,-,Task 3 - Block ICMP to US subnet
7,Block,-,-,-,10.0.40.0/24,1,-,-,Task 3 - Block ICMP to UK subnet
8,Block,-,-,-,10.0.20.0/24,1,-,-,Task 3 - Block ICMP to India subnet
9,Allow,-,-,10.0.0.0/24,10.0.1.0/24,1,-,-,Task 3 - Allow HQ to ping US subnet
10,Allow,-,-,10.0.0.0/24,10.0.40.0/24,1,-,-,Task 3 - Allow HQ to ping UK subnet
11,Allow,-,-,10.0.0.0/24,10.0.20.0/24,1,-,-,Task 3 - Allow HQ to ping India subnet

# Task 4: Block cn3 web server responses
12,Block,-,-,10.0.30.3/32,-,6,80,-,Task 4 - Block cn3 HTTP responses (source port 80)
13,Block,-,-,10.0.30.3/32,-,6,443,-,Task 4 - Block cn3 HTTPS responses (source port 443)

# Task 5: Block access to us3/us4 TCP 9520 using CIDR
14,Block,-,-,10.0.40.128/30,10.0.1.32/30,6,-,9520,Task 5 - Block uk2-uk5 from us3/us4 TCP 9520
15,Block,-,-,10.0.20.124/30,10.0.1.32/30,6,-,9520,Task 5 - Block in4-in5 from us3/us4 TCP 9520
16,Block,-,-,10.0.1.124/30,10.0.1.32/30,6,-,9520,Task 5 - Block us5 from us3/us4 TCP 9520
17,Block,-,-,10.0.0.220/30,10.0.1.32/30,6,-,9520,Task 5 - Block hq5 from us3/us4 TCP 9520

# Task 6: Block us1 MAC address on UDP (rogue Pi)
18,Block,00:00:00:01:00:1e,-,-,-,17,-,-,Task 6 - Block us1 MAC on UDP (rogue Pi)

# Task 7: Block world from TCP port 25 on all corporate subnets
19,Block,-,-,-,10.0.0.0/24,6,-,25,Task 7 - Block TCP port 25 to HQ
20,Block,-,-,-,10.0.1.0/24,6,-,25,Task 7 - Block TCP port 25 to US
21,Block,-,-,-,10.0.20.0/24,6,-,25,Task 7 - Block TCP port 25 to India
22,Block,-,-,-,10.0.30.0/24,6,-,25,Task 7 - Block TCP port 25 to China
23,Block,-,-,-,10.0.40.0/24,6,-,25,Task 7 - Block TCP port 25 to UK
```

### Packet Capture (packetcapture.pcap)

Used tshark to capture live traffic between two hosts on the simulated network — ICMP pings, a TCP connection on port 80, and a UDP connection on port 8000. Then opened it in Wireshark to look at the actual packet headers, which helped me understand exactly what fields the firewall rules need to match against.

## Test Results

Both test suites passed with full marks:

**Alternate test suite** — tests the engine against a known-good config (45/45):

![Alt Test Results](screenshots/alt-test-passed.png)

**Standard test suite** — tests my engine + my rules together (86/86):

![Standard Test Results](screenshots/standard-test-passed.png)

**POX controller loading all 23 rules:**

![POX Rules](screenshots/pox-rules-loaded.png)

## Other Screenshots

### VM setup — Mininet working
![VM Setup](screenshots/vm-setup.png)

### POX controller update
![POX Update](screenshots/pox-update.png)

### Wireshark capture in progress
![Packet Capture](screenshots/packet-capture.png)

### Capture complete — 82 packets
![Capture Complete](screenshots/capture-complete.png)

## Project Files

- `sdn-firewall.py` — the firewall engine that reads rules and creates OpenFlow flow mods
- `configure.pol` — all 23 firewall rules covering the 7 scenarios
- `packetcapture.pcap` — Wireshark capture of ICMP, TCP, and UDP traffic between simulated hosts (open in Wireshark to inspect the packet headers)

## Tools Used

- Mininet (network simulator)
- POX (OpenFlow SDN controller, Python)
- OpenFlow 1.0
- Wireshark / tshark
- Python 3
- VMware Workstation with Debian Bullseye VM