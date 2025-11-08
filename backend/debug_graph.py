"""Debug script to visualize the graph structure."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import parse_line_segments
from src.room_detector import build_wall_graph, detect_cycles
import networkx as nx

json_path = "../tests/sample_data/complex/complex_floorplan.json"
segments = parse_line_segments(json_path)

print("Wall Segments:")
for i, seg in enumerate(segments):
    print(f"  {i+1}: {seg.start} -> {seg.end}")

print("\nBuilding graph...")
graph = build_wall_graph(segments, tolerance=1.0)

print(f"\nGraph nodes: {len(graph.nodes())}")
print(f"Graph edges: {len(graph.edges())}")

print("\nNodes:")
for node in graph.nodes():
    print(f"  {node}")

print("\nEdges:")
for edge in graph.edges():
    print(f"  {edge}")

print("\nDetecting cycles...")
cycles = detect_cycles(graph)
print(f"Found {len(cycles)} cycles:")

for i, cycle in enumerate(cycles):
    print(f"\nCycle {i+1} ({len(cycle)} nodes):")
    for node in cycle:
        print(f"  {node}")

# Also try simple_cycles directly
print("\n\nTrying simple_cycles directly...")
directed = graph.to_directed()
all_simple = list(nx.simple_cycles(directed))
print(f"simple_cycles found {len(all_simple)} cycles:")
for i, cycle in enumerate(all_simple):
    if len(cycle) >= 3:  # Only show cycles with 3+ nodes
        print(f"  Cycle {i+1} ({len(cycle)} nodes): {cycle}")

