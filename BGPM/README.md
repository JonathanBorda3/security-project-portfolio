# BGP Measurements

Analyzed real-world BGP routing data from RIPE NCC route collectors to measure how the internet's routing table has evolved over time. The project uses pybgpstream to parse MRT/RIB dump files and extract metrics about prefix growth, AS-path lengths, route stability, and blackholing events.

## What It Does

The project has six analysis tasks that each look at a different aspect of BGP routing data:

**Routing Table Growth (Tasks 1A-1C)**
- Count unique IP prefixes per snapshot to see how the routing table has grown year over year
- Count unique autonomous systems to track how many networks are on the internet
- Identify the top 10 origin ASes by prefix growth — which networks are announcing the most new prefixes over time

**AS-Path Length Analysis (Task 2)**
- For every origin AS, find the shortest AS-path length across all peers in each snapshot
- Uses global dedup to remove AS-path prepending artifacts
- Tracks how path lengths evolve across snapshots — if an AS gets closer or farther from the observation point

**Route Stability (Task 3)**
- Parse BGP update messages to identify announcement/withdrawal pairs
- Measure how long a route stays announced before being withdrawn
- Each new announcement refreshes the timer, so the duration is from the most recent announcement to the withdrawal

**Blackholing Detection (Task 4)**
- Detect Remote Triggered Blackholing (RTBH) events by looking for the well-known `:666` community value
- Track how long blackholing events last — from the RTBH-tagged announcement until a withdrawal or non-RTBH announcement replaces it
- Non-RTBH announcements silently close the blackholing state without emitting a duration

## Data

The project processes BGP data from two RIPE NCC route collectors:
- **rrc04** — located at CIXP (Geneva)
- **rrc12** — located at DE-CIX (Frankfurt)

Each collector has:
- 8 RIB snapshot files spanning 2010-2017 (used for Tasks 1A, 1B, 1C, 2)
- 26 update files from a single day in January 2021 (used for Task 3)
- 50 update files with blackholing community tags (used for Task 4)

The RIB files are MRT format, gzip-compressed, ranging from 17MB to 100MB+ each.

## Interesting Things I Ran Into

The trickiest part was figuring out how AS-path length should be calculated. BGP routers do something called "AS-path prepending" where they repeat their AS number in the path to influence routing decisions. A raw path like `20932 3549 1239 721 27064 721 721 721 575 306 361` has AS 721 appearing multiple times — both as consecutive prepending AND as a loop (721 appears before and after 27064).

I initially used consecutive dedup (only removing back-to-back duplicates), which gave the wrong answer. The correct approach is global dedup — count each unique AS in the path only once, regardless of where it appears. That dropped my error count from 20,000+ mismatches to 0.

For the RTBH task, the state machine logic was the interesting part. A blackholing event opens when you see an announcement tagged with `:666`, but it doesn't close the same way as a regular AW event. If a non-RTBH announcement comes in for the same prefix, it silently replaces the blackholing state without recording a duration. Only a withdrawal actually emits the event duration.

## Results

Scored 98/100 on the autograder across both provided collectors and a hidden test dataset.

## Project Files

- bgpm.py — all six analysis functions
- screenshots/ — project structure and test results

## Tools

- Python 3
- pybgpstream (CAIDA's BGP Stream library)
- MRT/RIB dump files from RIPE NCC

## Note

I'm not including the BGP data files or the test harness in this repo since they're large binary files (~700MB total). The code is the interesting part — it shows how to work with real BGP routing data using pybgpstream's singlefile interface.
