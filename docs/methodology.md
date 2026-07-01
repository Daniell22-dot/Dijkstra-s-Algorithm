# Methodology & Algorithmic Framework

The engineering workflow transitions sequentially through four major development phases to satisfy all specific project objectives.

## Phase 1: 3D Asset Modeling & Pipeline Conversion (Objective 1)
1. **Architectural Drafting:** Build structural architectural representations of the campus blocks inside ArchiCAD, capturing rooms, walls, windows, doors, and staircases.
2. **Interoperability Export:** Save the semantic BIM files out as standard Industry Foundation Classes (IFC) or Wavefront OBJ files.
3. **3D Tiling:** Process the geometries through hierarchical Level of Detail (HLOD) compilers into OGC 3D Tiles. This compresses massive geometric files into spatial chunks easily digestible by standard web graphics cards.

## Phase 2: Database Modeling & Topology Configuration (Objective 2)
1. **Database Schema Creation:** Deploy a PostgreSQL instance and install the PostGIS geographic and pgRouting graph network extensions.
2. **Attribute Mapping:** Load structural properties (e.g., Room Area, Use Type, Capacity, Risk Index) mapped against explicit spatial spatial boundaries (`GEOMETRY` data classes with Z-aware elevations).
3. **Topology Topology Generation:** Map physical walkways to construct an indoor topological graph table (`network_edges`) where connecting pathways are registered as edges bounded by origin and destination vertices.

## Phase 3: Raycasting & Spatial Attributes Query (Objective 3)
1. **Viewport Scene Picking:** Bind mouse events to the CesiumJS rendering canvas context.
2. **Ray-Mesh Intersection:** Use the `scene.pick()` API to perform a mathematical raycast calculation from screen-space coordinates into the 3D spatial window coordinates.
3. **Asynchronous API Call:** Retrieve the targeted unique asset identifier (`room_id`) from the 3D Tile feature metadata, firing a non-blocking asynchronous background query to the database API layer to render the properties instantly inside an HTML details sidebar dashboard.

## Phase 4: Indoor Routing via Dijkstra's Algorithm (Objective 4)
The spatial graph routing engine uses Dijkstra's Shortest Path Algorithm to solve indoor navigational queries between distant rooms across multiple floors.

### Mathematical Logic Flow
To evaluate a route from starting point node ( A ) to ending point node ( B ), the network engine tracks a graph  G = (V, E) , where  V  is the set of topological room/door intersections (nodes) and  E  is the set of physical walkways (edges).

1. **Graph Weighting:** Every edge in the table is assigned a structural cost cost weight ( w ), representing the exact physical distance in meters between its terminal nodes.
2. **Distance Initialization:** The algorithm marks the path length distance value to the origin node ( A ) as  0 , while pre-setting all other network graph node distances to infinity ( \infty ).
3. **Iterative Node Relaxation:** The pathfinding process visits the closest unvisited neighboring node ( u ) and evaluates whether moving through  u  offers a faster path to an adjacent node ( v ). It updates values continually following the path relaxation formula: d(v) = min( d(v), d(u) + w(u, v) ) *Where* d(u) represents the accumulated distance to node u, and w(u,v) is the length weight of the edge line connecting node u to node v.
4. **Coordinate Array Outputs:** Once the destination room vertex (B) is marked resolved, the algorithm extracts the exact chain of traversed database nodes and passes a coordinate string array back to the web application frontend client.
5. **3D Line Vector Path Generation:** CesiumJS maps this array index dynamically, drawing a bright navigation polyline overlay cutting safely across open corridors and up vertical stairwells on the 3D visual campus environment.
