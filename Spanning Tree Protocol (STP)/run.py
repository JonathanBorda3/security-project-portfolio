#!/usr/bin/python

"""
Main execution script for Spanning Tree Protocol simulation

Usage:
    python run.py <topology_file>
    
Example:
    python run.py Sample
    python run.py ComplexLoopTopo
    
Note: topology file should NOT include the .py extension
"""

import sys
from Topology import *

PYTHON_VERSION = 3
PYTHON_RELEASE = 11

# Check python version
if sys.version_info < (PYTHON_VERSION, PYTHON_RELEASE):
    print("Warning:")
    print(f"    Please be sure you are using at least Python {PYTHON_VERSION}.{PYTHON_RELEASE}.x")
    exit()

if len(sys.argv) != 2:
    print("Syntax:")
    print("    python run.py <topology_file>")
    exit()

topology_file = sys.argv[1]
# Check topology_file
if topology_file.endswith('.py'):
    topology_file = topology_file[:-3]
    print("Syntax:")
    print("    Note that the topology parameter should not have the .py extension.")
    print("    Removing the '.py' extension...")

# Populate the topology
topo = Topology(topology_file)

# Run the topology
topo.run_spanning_tree()
# Close the logfile
topo.log_spanning_tree(f"{topology_file}.log")
