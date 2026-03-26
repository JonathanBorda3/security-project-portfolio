# Spanning Tree Protocol Implementation

A Python implementation of a simplified Spanning Tree Protocol that prevents loops in network topologies by building a loop-free tree structure. Each switch runs the algorithm independently and communicates with neighbors to agree on which links should be active.

## What This Does

The algorithm builds a spanning tree across an arbitrary Layer 2 network topology:
- Finds the root switch (lowest ID becomes root)
- Calculates shortest paths from each switch to the root
- Deactivates links that would create loops
- Handles network changes when switches are dropped

The interesting part was getting the distributed nature right - each switch only knows what its neighbors tell it, so the algorithm has to work regardless of message ordering or topology complexity.

## How It Works

Each switch maintains a view of the tree:
- **Root**: Which switch it thinks is the root
- **Distance**: How many hops to the root
- **Active Links**: Which neighbor connections are part of the tree
- **Switch Through**: Which neighbor is on the path to root

Switches exchange messages with their neighbors containing:
- Claimed root ID
- Distance to that root
- Whether the path goes through the recipient
- Time-to-live counter (for triggering topology changes)

The algorithm handles three main cases:

1. **Better root discovered**: Update to new root, recalculate distances
2. **Better path to current root**: Switch to shorter path
3. **Tie breaking**: When multiple equal paths exist, choose lowest neighbor ID

## Network Topologies Tested

| Topology | Switches | Loops | Drops | Notes |
|----------|----------|-------|-------|-------|
| Sample | 3 | None | None | Linear topology, baseline test |
| SimpleLoop | 4 | 1 | None | Square with one loop |
| NoLoop | 13 | None | 1 | Already a tree, tests drop handling |
| ComplexLoop | 13 | Multiple | 2 | Grid with multiple loops |
| TailTopo | 7 | 1 | 1 | Tests convergence after drop |

## Tricky Parts

**TTL Management**: The time-to-live counter isn't just for limiting propagation - it's used to trigger topology changes when switches get dropped. Getting this right required:
- Decrementing TTL with each message hop
- Continuing to send messages even when state doesn't change
- Using `>= 0` instead of `> 0` to allow TTL=0 messages through

**PathThrough Logic**: When a neighbor farther from the root sends `pathThrough=True`, it means they're a child node going through you to reach the root. You need to keep propagating messages to maintain that relationship, even though your own root/distance info didn't change.

**Outdated Root Info**: When a switch has old information about which switch is the root, you still need to check their `pathThrough` flag because the link state might be valid even if the root ID is wrong.

## Test Results

All provided test cases pass, including complex scenarios with multiple loops and switch drops:

- ✅ Sample topology (3 switches)
- ✅ SimpleLoop topology (4 switches, 1 loop)
- ✅ NoLoop topology (13 switches, 1 drop)
- ✅ ComplexLoop topology (13 switches, multiple loops, 2 drops)
- ✅ TailTopo (7 switches, 1 loop, 1 drop)
- ✅ Hidden test cases 1-3

The algorithm correctly:
- Identifies switch 1 as root in all topologies
- Builds loop-free spanning trees
- Handles switch drops and re-converges
- Breaks ties consistently using lowest neighbor ID

## What I Learned

This project really drove home how distributed algorithms work - there's no central controller, just switches running the same logic and passing messages. The challenge is making sure the algorithm converges correctly regardless of:
- Which messages arrive first
- Network topology complexity
- Switches being added or removed

The key insight was understanding that message propagation needs to continue even when a switch's state is stable, because other parts of the network might still be converging or the TTL needs to count down for topology changes.

## Tools Used

- Python 3.11
- Mininet (network emulation)
- Custom message passing framework
- Gradescope (automated testing)

## Project Files

```
Spanning-Tree-Protocol/
├── README.md                          # This file
├── Switch.py                          # Main STP implementation
├── switch-annotated.py                # Commented version explaining logic
├── Message.py                         # Message class definition
├── StpSwitch.py                       # Parent class with helper methods
├── Topology.py                        # Network topology manager
├── run.py                             # Main execution script
├── topologies/
│   ├── Sample.py                      # 3-switch linear topology
│   ├── SimpleLoopTopo.py              # 4-switch square
│   ├── NoLoopTopo.py                  # 13-switch tree
│   ├── ComplexLoopTopo.py             # 13-switch grid
│   └── TailTopo.py                    # 7-switch with tail
├── expected-outputs/
│   ├── Sample.log
│   ├── SimpleLoopTopo.log
│   ├── NoLoopTopo.log
│   ├── ComplexLoopTopo.log
│   └── TailTopo.log
└── screenshots/
    └── test-results.png               # Gradescope results showing 95/100
```

## Running the Code

```bash
python run.py Sample          # Run on Sample topology
python run.py ComplexLoopTopo # Run on complex topology
```

Output shows active links for each switch in the spanning tree.

---

*Note: This was a course project for Computer Networks. The core algorithm implementation (Switch.py) is my work and can be shared since the course has concluded. The framework files (Topology.py, Message.py, StpSwitch.py, run.py) were provided as part of the assignment infrastructure.*
