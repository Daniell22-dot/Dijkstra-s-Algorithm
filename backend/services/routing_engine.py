"""
Routing engine using Dijkstra algorithm
"""

import networkx as nx
from database import db
import json
import os
from config import Config


class RoutingEngine:
    """Routing engine for finding shortest paths"""
    
    def __init__(self):
        """Initialize the routing engine"""
        self.graph = None
        self.node_map = {}
        self._load_network()
    
    def _load_network(self):
        """Load network from database or file"""
        self.graph = nx.Graph()
        
        try:
            # Try to load from database
            nodes = db.execute_query("""
                SELECT id, name, floor, x, y, z, node_type, is_room
                FROM network_nodes
            """)
            
            edges = db.execute_query("""
                SELECT source, target, weight, floor, edge_type
                FROM network_edges
            """)
            
            if nodes and edges:
                # Add nodes
                for node in nodes:
                    self.graph.add_node(
                        node['id'],
                        name=node['name'],
                        floor=node['floor'],
                        x=node['x'],
                        y=node['y'],
                        z=node['z'],
                        type=node['node_type'],
                        is_room=node['is_room']
                    )
                    self.node_map[node['id']] = node['name']
                
                # Add edges
                for edge in edges:
                    self.graph.add_edge(
                        edge['source'],
                        edge['target'],
                        weight=edge['weight'],
                        floor=edge['floor'],
                        type=edge['edge_type']
                    )
                
                print(f"Loaded network: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
                return
        
        except Exception as e:
            print(f"Could not load from database: {e}")
        
        # Fallback: Load from JSON file
        self._load_from_json()
    
    def _load_from_json(self):
        """Load network from JSON file"""
        json_path = os.path.join(Config.ROUTING_DATA_DIR, 'network_graph.json')
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                for node in data['nodes']:
                    self.graph.add_node(
                        node['id'],
                        name=node['name'],
                        floor=node['floor'],
                        x=node['x'],
                        y=node['y'],
                        z=node['z'],
                        type=node.get('type', 'room'),
                        is_room=node.get('is_room', True)
                    )
                    self.node_map[node['id']] = node['name']
                
                for edge in data['edges']:
                    self.graph.add_edge(
                        edge['from'],
                        edge['to'],
                        weight=edge['weight'],
                        floor=edge.get('floor', 'unknown'),
                        type=edge.get('type', 'corridor')
                    )
                
                print(f" Loaded network from JSON: {self.graph.number_of_nodes()} nodes")
            
            except Exception as e:
                print(f" Failed to load network from JSON: {e}")
                self._create_sample_network()
        else:
            self._create_sample_network()
    
    def _create_sample_network(self):
        """Create a sample network for testing"""
        print(" Creating sample network...")
        
        # Sample nodes
        nodes = [
            {'id': 'R101', 'name': 'Room 101', 'floor': 'Ground', 'x': 0, 'y': 0, 'z': 0},
            {'id': 'R102', 'name': 'Room 102', 'floor': 'Ground', 'x': 10, 'y': 0, 'z': 0},
            {'id': 'R103', 'name': 'Room 103', 'floor': 'Ground', 'x': 20, 'y': 0, 'z': 0},
            {'id': 'R201', 'name': 'Room 201', 'floor': 'First', 'x': 0, 'y': 0, 'z': 3.5},
            {'id': 'R202', 'name': 'Room 202', 'floor': 'First', 'x': 10, 'y': 0, 'z': 3.5},
            {'id': 'R203', 'name': 'Room 203', 'floor': 'First', 'x': 20, 'y': 0, 'z': 3.5},
            {'id': 'Stair1', 'name': 'Stairway A', 'floor': 'Ground', 'x': 10, 'y': 5, 'z': 0},
            {'id': 'Stair2', 'name': 'Stairway A', 'floor': 'First', 'x': 10, 'y': 5, 'z': 3.5},
        ]
        
        # Sample edges
        edges = [
            {'from': 'R101', 'to': 'R102', 'weight': 5, 'floor': 'Ground'},
            {'from': 'R102', 'to': 'R103', 'weight': 5, 'floor': 'Ground'},
            {'from': 'R102', 'to': 'Stair1', 'weight': 3, 'floor': 'Ground'},
            {'from': 'Stair1', 'to': 'Stair2', 'weight': 2, 'floor': 'Transition'},
            {'from': 'Stair2', 'to': 'R201', 'weight': 4, 'floor': 'First'},
            {'from': 'Stair2', 'to': 'R202', 'weight': 3, 'floor': 'First'},
            {'from': 'R201', 'to': 'R202', 'weight': 5, 'floor': 'First'},
            {'from': 'R202', 'to': 'R203', 'weight': 5, 'floor': 'First'},
        ]
        
        for node in nodes:
            self.graph.add_node(
                node['id'],
                name=node['name'],
                floor=node['floor'],
                x=node['x'],
                y=node['y'],
                z=node['z'],
                type='room' if 'Room' in node['name'] else 'stair',
                is_room='Room' in node['name']
            )
            self.node_map[node['id']] = node['name']
        
        for edge in edges:
            self.graph.add_edge(
                edge['from'],
                edge['to'],
                weight=edge['weight'],
                floor=edge['floor'],
                type='corridor'
            )
        
        print(f" Created sample network: {self.graph.number_of_nodes()} nodes")
    
    def find_shortest_path(self, start_id, end_id):
        """
        Find the shortest path between two nodes
        
        Parameters:
        -----------
        start_id : str
            ID of the start room
        end_id : str
            ID of the end room
        
        Returns:
        --------
        dict : Path information
        """
        if start_id not in self.graph:
            return {'error': f'Start room "{start_id}" not found in network'}
        
        if end_id not in self.graph:
            return {'error': f'End room "{end_id}" not found in network'}
        
        try:
            # Find shortest path
            path = nx.shortest_path(
                self.graph,
                source=start_id,
                target=end_id,
                weight='weight'
            )
            
            # Calculate total distance
            total_distance = 0
            for i in range(len(path) - 1):
                total_distance += self.graph[path[i]][path[i+1]]['weight']
            
            # Get node details
            path_details = []
            for node_id in path:
                node_data = self.graph.nodes[node_id]
                path_details.append({
                    'id': node_id,
                    'name': node_data.get('name', node_id),
                    'floor': node_data.get('floor', 'unknown'),
                    'type': node_data.get('type', 'unknown'),
                    'x': node_data.get('x', 0),
                    'y': node_data.get('y', 0),
                    'z': node_data.get('z', 0)
                })
            
            return {
                'path': path,
                'path_details': path_details,
                'distance': round(total_distance, 2),
                'steps': len(path) - 1,
                'start': start_id,
                'end': end_id
            }
        
        except nx.NetworkXNoPath:
            return {'error': f'No path found between {start_id} and {end_id}'}
        except Exception as e:
            return {'error': str(e)}
    
    def validate_rooms(self, start_id, end_id):
        """Validate if rooms exist and are connected"""
        result = {
            'start_exists': start_id in self.graph,
            'end_exists': end_id in self.graph,
            'connected': False
        }
        
        if result['start_exists'] and result['end_exists']:
            try:
                nx.shortest_path(self.graph, start_id, end_id, weight='weight')
                result['connected'] = True
            except:
                result['connected'] = False
        
        return result
    
    def get_all_rooms(self):
        """Get all rooms in the network"""
        rooms = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get('is_room', False):
                rooms.append({
                    'id': node_id,
                    'name': data.get('name', node_id),
                    'floor': data.get('floor', 'unknown')
                })
        return sorted(rooms, key=lambda x: x['name'])
    