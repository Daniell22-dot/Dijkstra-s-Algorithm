#!/usr/bin/env python3
"""
Compute XYZ ENU coordinates for all rooms.

Transforms IFC local coordinates (from rooms.csv / network_graph.json)
into georeferenced ENU coordinates with correct altitude based on floor.

Transformation:
  1. Take local (x, y, z) coordinates (relative to building centre)
  2. Apply 270° yaw rotation: (x', y') = (y, -x)
  3. Map floor z-offset to absolute altitude:
       Ground   (z=0.1) -> 1772 m
       First    (z=3.1) -> 1775 m
       Second   (z=6.1) -> 1778 m
  4. Result has x_enu, y_enu, z_ENU in metres
"""

import json
import csv
import os
import sys

# Building altitude per floor (metres above ellipsoid)
FLOOR_ALTITUDES = {
    "Ground": 1772,
    "First": 1775,
    "Second": 1778,
}


def compute_xyz_from_csv(csv_path, output_path):
    """Compute XYZ coordinates from rooms.csv and write updated JSON."""
    rooms = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rooms.append(row)

    # Building centre: from the data, room coordinates are relative to the building centre.
    # The IFC centre is at (0,0,0) in the local coordinate system.
    cx, cy, cz = 0.0, 0.0, 0.0

    for room in rooms:
        # Local IFC coordinates
        xi = float(room["center_x"])
        yi = float(room["center_y"])
        zi = float(room["center_z"])

        # Floor mapping based on z offset
        if abs(zi - 0.1) < 0.01:
            floor = "Ground"
        elif abs(zi - 3.1) < 0.01:
            floor = "First"
        elif abs(zi - 6.1) < 0.01:
            floor = "Second"
        else:
            floor = "Ground"  # fallback

        # Translate by centre (centre at origin, so no change)
        dx, dy, dz = xi - cx, yi - cy, zi - cz

        # Rotate 270° yaw: (dx', dy') = (dy, -dx)
        dx_prime = dy
        dy_prime = -dx

        # Add centre back + altitude
        x_enu = dx_prime + cx  # = dy + 0 = dy
        y_enu = dy_prime + cy  # = -dx + 0 = -x
        # Use floor-based altitude instead of dz + alt
        z_enu = FLOOR_ALTITUDES.get(floor, 1772)

        room["x_enu"] = round(x_enu, 3)
        room["y_enu"] = round(y_enu, 3)
        room["z_enu"] = z_enu

    # Write updated rooms data
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rooms, f, indent=2)

    print("Computed XYZ for", len(rooms), "rooms")
    print("Written to:", output_path)
    # Print summary
    for r in rooms[:3]:
        print(" ", r["id"], ": x_enu=", r["x_enu"], ", y_enu=", r["y_enu"], ", z_enu=", r["z_enu"], "(", r["floor"], ")")


def compute_xyz_from_graph(graph_path, output_path):
    """Compute XYZ coordinates from network_graph.json and write updated graph."""
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # Building centre at origin
    cx, cy, cz = 0.0, 0.0, 0.0

    for node in graph["nodes"]:
        xi = node["x"]
        yi = node["y"]
        zi = node["z"]

        # Floor mapping based on z offset
        if abs(zi - 0.1) < 0.01:
            floor = "Ground"
        elif abs(zi - 3.1) < 0.01:
            floor = "First"
        elif abs(zi - 6.1) < 0.01:
            floor = "Second"
        else:
            floor = "Ground"

        # Translate by centre (origin)
        dx, dy, dz = xi - cx, yi - cy, zi - cz

        # Rotate 270° yaw: (dx', dy') = (dy, -dx)
        dx_prime = dy
        dy_prime = -dx

        # Add centre back + altitude
        x_enu = dx_prime + cx  # = dy
        y_enu = dy_prime + cy  # = -dx
        z_enu = FLOOR_ALTITUDES.get(floor, 1772)

        node["x_enu"] = round(x_enu, 3)
        node["y_enu"] = round(y_enu, 3)
        node["z_enu"] = z_enu

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print("Computed XYZ for", len(graph["nodes"]), "nodes")
    print("Written to:", output_path)
    for node in graph["nodes"][:3]:
        print(" ", node["id"], ": x_enu=", node["x_enu"], ", y_enu=", node["y_enu"], ", z_enu=", node["z_enu"], "(", node["floor"], ")")


if __name__ == "__main__":
    # Paths
    rooms_csv = "src/data/bim/rooms.csv"
    graph_json = "src/data/routing/network_graph.json"
    rooms_output = "src/data/routing/rooms_xyz.json"
    graph_output = "src/data/routing/network_graph_xyz.json"

    # Check which files exist
    if os.path.exists(rooms_csv):
        print("Processing rooms.csv...")
        compute_xyz_from_csv(rooms_csv, rooms_output)
    else:
        print("rooms.csv not found at", rooms_csv)

    print("")

    if os.path.exists(graph_json):
        print("Processing network_graph.json...")
        compute_xyz_from_graph(graph_json, graph_output)
    else:
        print("network_graph.json not found at", graph_json)

    print("")
    print("Done! You can now use the XYZ coordinates in your Cesium viewer.")