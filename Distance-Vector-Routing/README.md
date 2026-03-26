# Distance Vector Routing

## What This Is

A distributed Bellman-Ford routing algorithm implemented in Python. Each node in the network only knows about itself and its direct neighbors — it figures out the shortest paths to every other node by exchanging distance vectors with its neighbors over multiple rounds until everything stabilizes.

This was a project for my Computer Networks grad course at Georgia Tech. The setup simulates how autonomous systems (like ISPs) share routing information with each other.

## How It Works

The simulation runs in rounds:

1. Each node starts knowing itself (cost 0) and its direct outgoing neighbors at their link weights
2. Nodes send their distance vector to upstream neighbors — basically saying "here's what I can reach and how much it costs"
3. When a node gets a neighbor's DV, it checks if routing through that neighbor would be cheaper for any destination. If so, it updates its own table
4. If anything changed, the node re-advertises. If nothing changed, it stays quiet
5. Once every node's message queue is empty, the algorithm is done

The tricky part was understanding the difference between link direction for **traffic** vs **messages**. Links are directed (A→B means traffic flows from A to B), but nodes can pass messages in either direction regardless. So if A→B exists, B will advertise its DV *back to A* so A can learn what's reachable through B.

## Negative Cycles

Some topologies have negative cycles — a loop of directed links where the total weight is less than zero. Traffic could theoretically loop through these forever and the cost would keep decreasing. The fix is simple: costs are clamped at -99 (the project's version of negative infinity). Once -99 propagates through the network, everything converges and the algorithm terminates naturally.

## Topologies Tested

| Topology | Nodes | What It Tests |
|----------|-------|---------------|
| SimpleTopo | 5 | Bidirectional links, mix of positive/negative/zero weights |
| SingleLoopTopo | 5 | Positive cycle, a node with no outgoing links |
| SimpleNegativeCycleTopo | 5 | Negative cycle with multi-character node names |
| ComplexTopo | 13 | Multiple negative cycles, ISP-style relationships |

Grading also included hidden topologies with things like odd-length cycles, 26+ node networks, and nodes with only incoming or only outgoing links.

## Project Files

```
Distance-Vector-Routing/
├── README.md
└── DistanceVector.py       # the Bellman-Ford implementation (only file I wrote)
```

The other files in the project (Node.py, Topology.py, helpers.py, topology files) were provided by the course and aren't included here.

## Tools Used

- Python 3.10
- VS Code
- Gradescope
