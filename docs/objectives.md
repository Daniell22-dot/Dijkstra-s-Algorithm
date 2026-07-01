```markdown
# Project Objectives

## Development of a Web-Based 3D Web-GIS Campus Digital Twin for Smart Facility Management Using ArchiCAD, Python, and CesiumJS

---

## 1. Main Objective

To develop a web-based 3D Web-GIS campus digital twin that integrates Building Information Modeling (BIM) data from ArchiCAD with Geographic Information Systems (GIS) data, enabling 3D visualization, building information queries, and indoor routing through an accessible web platform.

---

## 2. Specific Objectives

### Objective 1: 3D Model Conversion
**To convert ArchiCAD building models into a web-viewable 3D format (3D Tiles) for visualization in CesiumJS**

**Description:**
- Export the building model from ArchiCAD in IFC format
- Convert IFC to 3D Tiles using Cesium ion or py3dtiles
- Ensure geometric and semantic data is preserved
- Load 3D Tiles into CesiumJS viewer

**Key Activities:**
1. Export BIM model from ArchiCAD as IFC
2. Extract building geometry and attributes
3. Convert IFC to 3D Tiles format
4. Optimize for web streaming
5. Test loading in CesiumJS

**Deliverables:**
- 3D Tiles dataset for the School of Engineering building
- CesiumJS viewer displaying the 3D model

---

### Objective 2: Spatial Database Creation
**To create a spatial database storing building elements (rooms, doors, windows) with their attributes and connectivity relationships**

**Description:**
- Set up PostgreSQL with PostGIS extension
- Design database schema for building elements
- Import BIM attributes (room numbers, areas, floors, types)
- Store connectivity relationships for routing

**Key Activities:**
1. Install and configure PostgreSQL/PostGIS
2. Design tables: rooms, doors, windows, floors, nodes, edges
3. Import building attribute data from CSV/JSON
4. Create spatial indexes for performance
5. Enable pgRouting for shortest path queries

**Deliverables:**
- PostgreSQL database with complete building data
- Spatial indexes for efficient queries
- pgRouting enabled for routing

**Database Schema:**

```sql
-- Rooms table
CREATE TABLE rooms (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    floor VARCHAR(20) NOT NULL,
    type VARCHAR(50),
    area NUMERIC(10, 2),
    capacity INTEGER,
    equipment TEXT,
    year_built INTEGER,
    maintenance_status VARCHAR(20),
    risk_level VARCHAR(20),
    temperature NUMERIC(5, 2),
    noise_db INTEGER,
    lighting_lux INTEGER,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7)
);

-- Network nodes for routing
CREATE TABLE network_nodes (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    floor VARCHAR(20) NOT NULL,
    x NUMERIC(10, 2),
    y NUMERIC(10, 2),
    z NUMERIC(10, 2),
    is_room BOOLEAN DEFAULT TRUE
);

-- Network edges for routing
CREATE TABLE network_edges (
    id SERIAL PRIMARY KEY,
    source VARCHAR(20) REFERENCES network_nodes(id),
    target VARCHAR(20) REFERENCES network_nodes(id),
    weight NUMERIC(10, 2),
    floor VARCHAR(20)
);