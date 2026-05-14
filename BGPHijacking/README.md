# BGP Hijacking

A BGP hijacking simulation I built in Mininet for a graduate Computer Networks course. I configured a 6-AS network topology with FRR routing daemons and demonstrated both a simple prefix hijack and an advanced more-specific-prefix hijack that captures traffic across the entire network.

## What This Project Does

BGP is how autonomous systems on the internet exchange routing information. The problem is that BGP trusts route advertisements by default — there's no built-in authentication. So a malicious AS can announce someone else's IP prefix and steal their traffic.

I built a Mininet simulation of a 6-AS network based on a topology from a BGP hijacking research paper. Each AS runs its own FRR routing daemon with zebra (interface/IP management) and bgpd (BGP peering and route advertisements). A legitimate web server runs on AS1, and a rogue web server runs on AS6 — when the hijack succeeds, you see the attacker's response instead of the legitimate one.

## Network Architecture

| AS | Router | Prefix | Role |
|----|--------|--------|------|
| AS1 | R1 | 11.0.0.0/8 | True origin (victim) |
| AS2 | R2 | 12.0.0.0/8 | Transit AS |
| AS3 | R3 | 13.0.0.0/8 | Transit AS |
| AS4 | R4 | 14.0.0.0/8 | Transit AS |
| AS5 | R5 | 15.0.0.0/8 | Transit AS |
| AS6 | R6 | 11.0.0.0/8 | Rogue AS (attacker) |

Peering links: AS1–AS2, AS1–AS3, AS2–AS3, AS2–AS4, AS2–AS5, AS3–AS4, AS3–AS5, AS4–AS5, AS5–AS6

## The Two Attacks

### Part 1: Simple Prefix Hijack

AS6 advertises AS1's prefix (11.0.0.0/8) to its neighbor AS5. Since AS6 is directly connected to AS5, the path through AS6 is shorter than the multi-hop path to AS1 for some parts of the network. Hosts on AS5 see the attacker's web server instead of the legitimate one.

### Part 2: Advanced Prefix Hijack

The simple attack doesn't fool ASes that are closer to AS1 than to AS6 (like AS2, which is directly connected to AS1). To hijack the whole network, AS6 advertises a more specific prefix — 11.0.0.0/9 instead of /8. BGP always prefers more specific routes regardless of path length, so every AS in the network (except AS1 itself) routes 11.0.x.x traffic through AS6.

This is the same technique used in real-world incidents like the 2017 Russian telecom hijack of financial services traffic and the 2022 KLAYswap cryptocurrency theft.

## What I Learned

The tricky part was getting all the IP addressing right across 6 routers with 9 inter-router links. Every zebra interface IP has to match the corresponding bgpd neighbor statement on the peer router, and Mininet assigns interface numbers based on the order you create links in code — so if the addLink order doesn't match your zebra configs, nothing peers correctly.

I also didn't expect the BGP tiebreaking behavior to matter so much. When two routes have the same prefix and same path length, BGP falls back to things like router ID and route age to pick a winner. Understanding those tiebreakers was key to getting the simple attack working.

## Tools Used

- Python
- Mininet (network emulator)
- FRR (Free Range Routing) — zebra + bgpd
- Linux networking (ip, ifconfig, route)
- Shell scripting (bash)

## Academic Integrity

This was a graded project for a Georgia Tech graduate course. I'm not sharing the configuration files or code publicly — this README describes what I built and what I learned. If you're a current student, please do your own work.
