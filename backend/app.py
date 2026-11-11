import os
import json
import math
import subprocess
import networkx as nx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__, static_folder='../src')
CORS(app)

# Database-backed API (rooms, routing, buildings)
from routes import rooms_bp, routing_bp, buildings_bp

app.register_blueprint(rooms_bp)
app.register_blueprint(routing_bp)
app.register_blueprint(buildings_bp)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
UPLOAD_FOLDER = '../storage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

REGISTRY_FILE = os.path.join(UPLOAD_FOLDER, 'campus_registry.json')

# BUILDING REGISTRY

def load_registry():
    """Load the campus building registry"""
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_registry(registry):
    """Save the campus building registry"""
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)

# HEALTH CHECK

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'DeKUT Campus Digital Twin API',
        'version': '1.0.0'
    })


# FRONTEND CONFIG

@app.route('/api/config', methods=['GET'])
def get_config():
    """Expose non-secret frontend configuration."""
    return jsonify({
        'status': 'success',
        'data': {
            'cesiumIonToken': Config.CESIUM_ION_TOKEN
        }
    })


@app.route('/api/config.js', methods=['GET'])
def get_config_js():
    """Serve the Cesium token as a classic script for static pages."""
    body = f"window.CESIUM_ION_TOKEN = {json.dumps(Config.CESIUM_ION_TOKEN)};\n"
    return body, 200, {'Content-Type': 'application/javascript; charset=utf-8'}

# GET ALL BUILDINGS

@app.route('/api/buildings', methods=['GET'])
def get_buildings():
    """Get all registered buildings"""
    registry = load_registry()
    return jsonify({
        'status': 'success',
        'data': registry
    })

# UPLOAD ENDPOINT

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    """
    Handle IFC file upload and processing
    Multi-user: Each building gets its own folder
    """
    
    building_id = request.form.get('building_id')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    elevation = request.form.get('elevation', '0')
    north_rotation = request.form.get('north_rotation', '0')
    
    if not building_id or not latitude or not longitude:
        return jsonify({
            'status': 'error',
            'message': 'Building ID, latitude, and longitude are required'
        }), 400
    
    file = request.files.get('file')
    if not file or not file.filename.endswith('.ifc'):
        return jsonify({
            'status': 'error',
            'message': 'Please upload a valid .ifc file'
        }), 400
    
    try:
        # Create isolated folder for this building
        building_folder = os.path.join(UPLOAD_FOLDER, secure_filename(building_id))
        os.makedirs(building_folder, exist_ok=True)
        
        # Save the uploaded IFC
        ifc_path = os.path.join(building_folder, 'model.ifc')
        file.save(ifc_path)
        
        # Step 1: Convert IFC to 3D Tiles using ifc23dtiles
        tileset_folder = os.path.join(building_folder, 'tileset')
        os.makedirs(tileset_folder, exist_ok=True)
        
        try:
            subprocess.run([
                'npx', 'ifc23dtiles',
                '-i', ifc_path,
                '-o', tileset_folder
            ], check=True, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return jsonify({
                'status': 'error',
                'message': '3D Tiles conversion timed out (large file)'
            }), 500
        except subprocess.CalledProcessError as e:
            return jsonify({
                'status': 'error',
                'message': f'3D Tiles conversion failed: {e.stderr}'
            }), 500
        
        # Step 2: Build routing network using Python
        routing_graph = build_routing_network(ifc_path)
        routing_path = os.path.join(building_folder, 'routing_graph.json')
        with open(routing_path, 'w') as f:
            json.dump(routing_graph, f, indent=2)
        
        # Step 3: Register the building
        registry = load_registry()
        registry[building_id] = {
            'lat': float(latitude),
            'lon': float(longitude),
            'alt': float(elevation),
            'north_rotation': float(north_rotation),
            'tileset_url': f'/static/{building_id}/tileset/tileset.json',
            'routing_url': f'/static/{building_id}/routing_graph.json',
            'uploaded': True
        }
        save_registry(registry)
        
        return jsonify({
            'status': 'success',
            'message': f'Building {building_id} processed successfully',
            'tileset_url': f'/static/{building_id}/tileset/tileset.json',
            'routing_url': f'/static/{building_id}/routing_graph.json',
            'building_data': registry[building_id]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ROUTING NETWORK BUILDER (3D Coordinates)

def build_routing_network(ifc_path):
    """
    Build a 3D routing network from IFC file
    Extracts rooms (nodes) and connections (edges) with 3D coordinates
    """
    try:
        import ifcopenshell
        from ifcopenshell import geom
        
        ifc_file = ifcopenshell.open(ifc_path)
        
        nodes = []
        edges = []
        floor_map = {}
        
        # Extract building storeys
        storeys = ifc_file.by_type('IfcBuildingStorey')
        for storey in storeys:
            floor_map[storey.GlobalId] = {
                'name': storey.Name or '0',
                'elevation': storey.Elevation or 0
            }
        
        # Extract spaces (rooms)
        spaces = ifc_file.by_type('IfcSpace')
        
        for space in spaces:
            try:
                # Get space center using geometry
                settings = geom.settings()
                settings.set(geom.SETTINGS_USE_WORLD_COORDS, True)
                shape = geom.create_shape(settings, space)
                vertices = shape.geometry.vertices
                
                # Calculate centroid
                if len(vertices) >= 3:
                    xs = [vertices[i] for i in range(0, len(vertices), 3)]
                    ys = [vertices[i+1] for i in range(0, len(vertices), 3)]
                    zs = [vertices[i+2] for i in range(0, len(vertices), 3)]
                    
                    center_x = sum(xs) / len(xs)
                    center_y = sum(ys) / len(ys)
                    center_z = sum(zs) / len(zs)
                else:
                    center_x, center_y, center_z = 0, 0, 0
                
                # Get floor level
                floor_name = "0"
                floor_elevation = 0
                for rel in space.ContainedInStructure:
                    if rel.is_a('IfcRelContainedInSpatialStructure'):
                        container = rel.RelatingStructure
                        if container.is_a('IfcBuildingStorey'):
                            floor_name = container.Name or "0"
                            floor_elevation = container.Elevation or 0
                            break
                
                nodes.append({
                    'id': space.GlobalId,
                    'name': space.Name or f'Room_{len(nodes)+1}',
                    'floor': str(floor_name),
                    'floor_elevation': float(floor_elevation),
                    'x': float(center_x),
                    'y': float(center_y),
                    'z': float(center_z),
                    'is_room': True,
                    'type': get_space_type(space)
                })
            except Exception as e:
                print(f"Error processing space: {e}")
                continue
        
        # Extract doors (connections between spaces)
        doors = ifc_file.by_type('IfcDoor')
        for door in doors:
            connected_spaces = []
            for rel in door.ConnectedFrom:
                if rel.is_a('IfcRelConnectsElements'):
                    if rel.RelatingElement and rel.RelatingElement.is_a('IfcSpace'):
                        connected_spaces.append(rel.RelatingElement.GlobalId)
                    if rel.RelatedElement and rel.RelatedElement.is_a('IfcSpace'):
                        connected_spaces.append(rel.RelatedElement.GlobalId)
            
            if len(connected_spaces) >= 2:
                from_id = connected_spaces[0]
                to_id = connected_spaces[1]
                
                # Find nodes
                from_node = next((n for n in nodes if n['id'] == from_id), None)
                to_node = next((n for n in nodes if n['id'] == to_id), None)
                
                if from_node and to_node:
                    dx = from_node['x'] - to_node['x']
                    dy = from_node['y'] - to_node['y']
                    dz = from_node['z'] - to_node['z']
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    edges.append({
                        'from': from_id,
                        'to': to_id,
                        'weight': float(distance) if distance > 0 else 1.0,
                        'floor': from_node['floor'],
                        'type': 'door'
                    })
        
        # Connect rooms on same floor via corridors (if within distance)
        for i, node1 in enumerate(nodes):
            if not node1.get('is_room', True):
                continue
            for node2 in nodes[i+1:]:
                if not node2.get('is_room', True):
                    continue
                if node1['floor'] != node2['floor']:
                    continue
                
                dx = node1['x'] - node2['x']
                dy = node1['y'] - node2['y']
                dz = node1['z'] - node2['z']
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                
                if distance < 20 and distance > 0:
                    edges.append({
                        'from': node1['id'],
                        'to': node2['id'],
                        'weight': float(distance),
                        'floor': node1['floor'],
                        'type': 'corridor'
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'floors': list(set(n['floor'] for n in nodes))
        }
        
    except ImportError:
        return create_sample_network()
    except Exception as e:
        print(f"Error building network: {e}")
        return create_sample_network()

def get_space_type(space):
    """Determine space type from name"""
    try:
        name = (space.Name or "").lower()
        if 'lecture' in name or 'class' in name:
            return 'Lecture Hall'
        elif 'lab' in name or 'laboratory' in name:
            return 'Laboratory'
        elif 'office' in name:
            return 'Office'
        elif 'conference' in name:
            return 'Conference Room'
        elif 'workshop' in name:
            return 'Workshop'
        elif 'corridor' in name or 'hall' in name:
            return 'Corridor'
        elif 'stair' in name:
            return 'Stairway'
        elif 'toilet' in name or 'restroom' in name:
            return 'Restroom'
        else:
            return 'Space'
    except:
        return 'Space'

def create_sample_network():
    """Create a sample 3D network for testing"""
    return {
        'nodes': [
            {'id': 'R101', 'name': 'Room 101', 'floor': 'Ground', 'floor_elevation': 0, 'x': 0, 'y': 0, 'z': 0, 'is_room': True, 'type': 'Lecture Hall'},
            {'id': 'R102', 'name': 'Room 102', 'floor': 'Ground', 'floor_elevation': 0, 'x': 10, 'y': 0, 'z': 0, 'is_room': True, 'type': 'Computer Lab'},
            {'id': 'R103', 'name': 'Room 103', 'floor': 'Ground', 'floor_elevation': 0, 'x': 20, 'y': 0, 'z': 0, 'is_room': True, 'type': 'Workshop'},
            {'id': 'R201', 'name': 'Room 201', 'floor': 'First', 'floor_elevation': 4.2, 'x': 0, 'y': 0, 'z': 4.2, 'is_room': True, 'type': 'Lecture Hall'},
            {'id': 'R202', 'name': 'Room 202', 'floor': 'First', 'floor_elevation': 4.2, 'x': 10, 'y': 0, 'z': 4.2, 'is_room': True, 'type': 'Office'},
            {'id': 'R203', 'name': 'Room 203', 'floor': 'First', 'floor_elevation': 4.2, 'x': 20, 'y': 0, 'z': 4.2, 'is_room': True, 'type': 'Conference Room'},
            {'id': 'R301', 'name': 'Room 301', 'floor': 'Second', 'floor_elevation': 8.4, 'x': 0, 'y': 0, 'z': 8.4, 'is_room': True, 'type': 'Research Lab'},
            {'id': 'R302', 'name': 'Room 302', 'floor': 'Second', 'floor_elevation': 8.4, 'x': 10, 'y': 0, 'z': 8.4, 'is_room': True, 'type': 'Design Studio'},
            {'id': 'Stair1', 'name': 'Stairway Ground', 'floor': 'Ground', 'floor_elevation': 0, 'x': 10, 'y': 5, 'z': 0, 'is_room': False, 'type': 'Stairway'},
            {'id': 'Stair2', 'name': 'Stairway First', 'floor': 'First', 'floor_elevation': 4.2, 'x': 10, 'y': 5, 'z': 4.2, 'is_room': False, 'type': 'Stairway'},
            {'id': 'Stair3', 'name': 'Stairway Second', 'floor': 'Second', 'floor_elevation': 8.4, 'x': 10, 'y': 5, 'z': 8.4, 'is_room': False, 'type': 'Stairway'},
        ],
        'edges': [
            {'from': 'R101', 'to': 'R102', 'weight': 5, 'floor': 'Ground', 'type': 'corridor'},
            {'from': 'R102', 'to': 'R103', 'weight': 5, 'floor': 'Ground', 'type': 'corridor'},
            {'from': 'R102', 'to': 'Stair1', 'weight': 3, 'floor': 'Ground', 'type': 'corridor'},
            {'from': 'Stair1', 'to': 'Stair2', 'weight': 2, 'floor': 'Transition', 'type': 'stair'},
            {'from': 'Stair2', 'to': 'R201', 'weight': 4, 'floor': 'First', 'type': 'corridor'},
            {'from': 'Stair2', 'to': 'R202', 'weight': 3, 'floor': 'First', 'type': 'corridor'},
            {'from': 'R201', 'to': 'R202', 'weight': 5, 'floor': 'First', 'type': 'corridor'},
            {'from': 'R202', 'to': 'R203', 'weight': 5, 'floor': 'First', 'type': 'corridor'},
            {'from': 'Stair2', 'to': 'Stair3', 'weight': 2, 'floor': 'Transition', 'type': 'stair'},
            {'from': 'Stair3', 'to': 'R301', 'weight': 4, 'floor': 'Second', 'type': 'corridor'},
            {'from': 'Stair3', 'to': 'R302', 'weight': 3, 'floor': 'Second', 'type': 'corridor'},
            {'from': 'R301', 'to': 'R302', 'weight': 5, 'floor': 'Second', 'type': 'corridor'},
        ],
        'floors': ['Ground', 'First', 'Second']
    }

# ROUTING API ENDPOINT (Dijkstra with 3D)

@app.route('/api/route', methods=['POST'])
def calculate_route():
    """
    Calculate shortest path using Dijkstra's algorithm
    Supports 3D coordinates for multi-storey routing
    """
    
    data = request.json
    building_id = data.get('building_id')
    start_id = data.get('start')
    end_id = data.get('end')
    
    if not building_id or not start_id or not end_id:
        return jsonify({
            'status': 'error',
            'message': 'building_id, start, and end are required'
        }), 400
    
    # Load the building's routing graph
    routing_path = os.path.join(UPLOAD_FOLDER, building_id, 'routing_graph.json')
    
    if not os.path.exists(routing_path):
        return jsonify({
            'status': 'error',
            'message': f'Building {building_id} routing graph not found'
        }), 404
    
    with open(routing_path, 'r') as f:
        graph_data = json.load(f)
    
    # Build NetworkX graph with 3D coordinates
    G = nx.Graph()
    
    # Add nodes
    for node in graph_data.get('nodes', []):
        G.add_node(
            node['id'],
            name=node.get('name', node['id']),
            floor=node.get('floor', 'unknown'),
            floor_elevation=node.get('floor_elevation', 0),
            x=node.get('x', 0),
            y=node.get('y', 0),
            z=node.get('z', 0),
            is_room=node.get('is_room', True),
            type=node.get('type', 'Room')
        )
    
    # Add edges
    for edge in graph_data.get('edges', []):
        G.add_edge(
            edge['from'],
            edge['to'],
            weight=edge.get('weight', 1.0),
            floor=edge.get('floor', 'unknown'),
            type=edge.get('type', 'corridor')
        )
    
    # Check if nodes exist
    if start_id not in G:
        return jsonify({'status': 'error', 'message': f'Start node {start_id} not found'}), 404
    if end_id not in G:
        return jsonify({'status': 'error', 'message': f'End node {end_id} not found'}), 404
    
    try:
        # Dijkstra's algorithm via NetworkX
        path = nx.shortest_path(G, source=start_id, target=end_id, weight='weight')
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(path) - 1):
            total_distance += G[path[i]][path[i+1]]['weight']
        
        # Get path details with 3D coordinates
        path_details = []
        for node_id in path:
            node_data = G.nodes[node_id]
            path_details.append({
                'id': node_id,
                'name': node_data.get('name', node_id),
                'floor': node_data.get('floor', 'unknown'),
                'floor_elevation': node_data.get('floor_elevation', 0),
                'x': node_data.get('x', 0),
                'y': node_data.get('y', 0),
                'z': node_data.get('z', 0),
                'type': node_data.get('type', 'Room')
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'path': path,
                'path_details': path_details,
                'distance': round(total_distance, 2),
                'steps': len(path) - 1,
                'start': start_id,
                'end': end_id,
                'floors': list(set(n['floor'] for n in path_details))
            }
        })
        
    except nx.NetworkXNoPath:
        return jsonify({
            'status': 'error',
            'message': 'No path found between these rooms'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# SERVE STATIC FILES

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ROOT ENDPOINT

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'DeKUT Campus Digital Twin API',
        'version': '1.0.0',
        'objectives': {
            'main': 'Develop web-based 3D Web-GIS campus digital twin',
            'specific_1': 'Convert ArchiCAD models to 3D Tiles for CesiumJS',
            'specific_2': 'Create spatial database for building elements',
            'specific_3': 'Develop routing engine using Dijkstra\'s algorithm'
        },
        'endpoints': {
            'health': '/api/health',
            'buildings': '/api/buildings',
            'upload': '/api/upload (POST)',
            'route': '/api/route (POST)',
            'rooms': '/api/v1/rooms',
            'routing': '/api/v1/routing'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)