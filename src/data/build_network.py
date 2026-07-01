"""
Build indoor routing network from BIM data
Creates nodes (rooms) and edges (connections via doors/corridors)
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import networkx as nx
import warnings
warnings.filterwarnings('ignore')


class NetworkBuilder:
    """
    Build indoor routing network from BIM data
    Nodes = rooms, Edges = connections (doors, corridors, stairs)
    """
    
    def __init__(self, data_dir="src/data/bim/"):
        """
        Initialize the network builder
        
        Parameters:
        -----------
        data_dir : str
            Directory containing BIM data CSV files
        """
        self.data_dir = data_dir
        self.rooms = None
        self.doors = None
        self.windows = None
        self.floors = None
        self.network = None
        self.nodes = []
        self.edges = []
        
    def load_bim_data(self):
        """
        Load BIM data from CSV files
        """
        print(" Loading BIM data...")
        
        # Load rooms
        rooms_path = os.path.join(self.data_dir, "rooms.csv")
        if os.path.exists(rooms_path):
            self.rooms = pd.read_csv(rooms_path)
            print(f"    Loaded {len(self.rooms)} rooms")
        else:
            print("     rooms.csv not found, creating sample data...")
            self._create_sample_data()
            return self.load_bim_data()
        
        # Load doors
        doors_path = os.path.join(self.data_dir, "doors.csv")
        if os.path.exists(doors_path):
            self.doors = pd.read_csv(doors_path)
            print(f"    Loaded {len(self.doors)} doors")
        
        # Load windows (for reference)
        windows_path = os.path.join(self.data_dir, "windows.csv")
        if os.path.exists(windows_path):
            self.windows = pd.read_csv(windows_path)
            print(f"    Loaded {len(self.windows)} windows")
        
        # Load floors
        floors_path = os.path.join(self.data_dir, "floors.csv")
        if os.path.exists(floors_path):
            self.floors = pd.read_csv(floors_path)
            print(f"    Loaded {len(self.floors)} floors")
        
        return self.rooms, self.doors
    
    def _create_sample_data(self):
        """
        Create sample data if CSV files don't exist
        """
        print(" Creating sample data for network...")
        
        # Sample rooms
        rooms = pd.DataFrame([
            {'id': 'R101', 'name': 'Room 101', 'floor': '1', 
             'area': 45, 'center_x': 0, 'center_y': 0, 'center_z': 1.5,
             'type': 'Lecture Hall'},
            {'id': 'R102', 'name': 'Room 102', 'floor': '1', 
             'area': 38, 'center_x': 10, 'center_y': 0, 'center_z': 1.5,
             'type': 'Computer Lab'},
            {'id': 'R103', 'name': 'Room 103', 'floor': '1', 
             'area': 60, 'center_x': 20, 'center_y': 0, 'center_z': 1.5,
             'type': 'Workshop'},
            {'id': 'R201', 'name': 'Room 201', 'floor': '2', 
             'area': 45, 'center_x': 0, 'center_y': 0, 'center_z': 4.5,
             'type': 'Lecture Hall'},
            {'id': 'R202', 'name': 'Room 202', 'floor': '2', 
             'area': 18, 'center_x': 10, 'center_y': 0, 'center_z': 4.5,
             'type': 'Office'},
            {'id': 'R203', 'name': 'Room 203', 'floor': '2', 
             'area': 30, 'center_x': 20, 'center_y': 0, 'center_z': 4.5,
             'type': 'Conference Room'},
            {'id': 'R301', 'name': 'Room 301', 'floor': '3', 
             'area': 42, 'center_x': 0, 'center_y': 0, 'center_z': 7.5,
             'type': 'Research Lab'},
            {'id': 'R302', 'name': 'Room 302', 'floor': '3', 
             'area': 35, 'center_x': 10, 'center_y': 0, 'center_z': 7.5,
             'type': 'Design Studio'},
        ])
        
        # Sample doors
        doors = pd.DataFrame([
            {'id': 'D101', 'name': 'Main Entrance', 'floor': '0'},
            {'id': 'D102', 'name': 'Side Entrance', 'floor': '0'},
            {'id': 'D103', 'name': 'Room 101 Door', 'floor': '1'},
            {'id': 'D104', 'name': 'Room 102 Door', 'floor': '1'},
            {'id': 'D105', 'name': 'Room 201 Door', 'floor': '2'},
            {'id': 'D106', 'name': 'Room 202 Door', 'floor': '2'},
        ])
        
        # Sample floors
        floors = pd.DataFrame([
            {'id': 'F0', 'name': 'Ground Floor', 'level': '0'},
            {'id': 'F1', 'name': 'First Floor', 'level': '1'},
            {'id': 'F2', 'name': 'Second Floor', 'level': '2'},
            {'id': 'F3', 'name': 'Third Floor', 'level': '3'},
        ])
        
        # Save to CSV
        os.makedirs(self.data_dir, exist_ok=True)
        rooms.to_csv(os.path.join(self.data_dir, "rooms.csv"), index=False)
        doors.to_csv(os.path.join(self.data_dir, "doors.csv"), index=False)
        floors.to_csv(os.path.join(self.data_dir, "floors.csv"), index=False)
        
        print(" Sample data created")
        
        # Set the data
        self.rooms = rooms
        self.doors = doors
        self.floors = floors
    
    def create_network_nodes(self):
        """
        Create nodes for the network
        Each room becomes a node
        """
        print(" Creating network nodes...")
        
        nodes = []
        for _, room in self.rooms.iterrows():
            node = {
                'id': room['id'],
                'name': room['name'],
                'floor': str(room['floor']),
                'x': float(room.get('center_x', 0)),
                'y': float(room.get('center_y', 0)),
                'z': float(room.get('center_z', 0)),
                'type': room.get('type', 'Room'),
                'area': room.get('area', 0),
                'is_room': True
            }
            nodes.append(node)
        
        # Add stairway nodes (transition between floors)
        floors = sorted(self.rooms['floor'].unique())
        if len(floors) > 1:
            for i, floor in enumerate(floors):
                stair_id = f"Stair_{floor}"
                # Find a central position for stairs on this floor
                floor_rooms = self.rooms[self.rooms['floor'] == floor]
                if not floor_rooms.empty:
                    avg_x = floor_rooms['center_x'].mean()
                    avg_y = floor_rooms['center_y'].mean()
                    avg_z = floor_rooms['center_z'].mean()
                    node = {
                        'id': stair_id,
                        'name': f'Stairway {floor}',
                        'floor': str(floor),
                        'x': float(avg_x + 5),
                        'y': float(avg_y + 5),
                        'z': float(avg_z),
                        'type': 'Stairway',
                        'area': 0,
                        'is_room': False,
                        'is_stair': True
                    }
                    nodes.append(node)
        
        self.nodes = nodes
        print(f"    Created {len(nodes)} nodes")
        return self.nodes
    
    def create_network_edges(self):
        """
        Create edges for the network
        Connects rooms through doors and corridors
        """
        print("🔗 Creating network edges...")
        
        edges = []
        
        # Group rooms by floor
        rooms_by_floor = {}
        for node in self.nodes:
            if node.get('is_room', False):
                floor = node['floor']
                if floor not in rooms_by_floor:
                    rooms_by_floor[floor] = []
                rooms_by_floor[floor].append(node)
        
        # Connect rooms on the same floor (through doors/corridors)
        for floor, floor_rooms in rooms_by_floor.items():
            # Sort rooms by position
            for i, room1 in enumerate(floor_rooms):
                for j, room2 in enumerate(floor_rooms):
                    if i >= j:
                        continue
                    
                    # Calculate distance between rooms
                    dx = room1['x'] - room2['x']
                    dy = room1['y'] - room2['y']
                    dist = np.sqrt(dx*dx + dy*dy)
                    
                    # Connect if within reasonable distance (corridor)
                    if dist < 15:
                        edge = {
                            'from': room1['id'],
                            'to': room2['id'],
                            'weight': dist,
                            'floor': floor,
                            'type': 'corridor'
                        }
                        edges.append(edge)
        
        stair_nodes = [n for n in self.nodes if n.get('is_stair', False)]
        sorted_stairs = sorted(stair_nodes, key=lambda x: int(x['floor']))
        
        for i in range(len(sorted_stairs) - 1):
            stair1 = sorted_stairs[i]
            stair2 = sorted_stairs[i + 1]
            
            
            for room in self.nodes:
                if room.get('is_room', False) and room['floor'] == stair1['floor']:
                    dx = room['x'] - stair1['x']
                    dy = room['y'] - stair1['y']
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < 10:
                        edges.append({
                            'from': room['id'],
                            'to': stair1['id'],
                            'weight': dist,
                            'floor': stair1['floor'],
                            'type': 'to_stair'
                        })
                
                if room.get('is_room', False) and room['floor'] == stair2['floor']:
                    dx = room['x'] - stair2['x']
                    dy = room['y'] - stair2['y']
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < 10:
                        edges.append({
                            'from': room['id'],
                            'to': stair2['id'],
                            'weight': dist,
                            'floor': stair2['floor'],
                            'type': 'to_stair'
                        })
            
            
            edges.append({
                'from': stair1['id'],
                'to': stair2['id'],
                'weight': 2.0,  
                'floor': 'transition',
                'type': 'stair'
            })
        
        self.edges = edges
        print(f"    Created {len(edges)} edges")
        return self.edges
    
    def build_networkx_graph(self):
        """
        Build a NetworkX graph from nodes and edges
        """
        print(" Building NetworkX graph...")
        
        G = nx.Graph()
        
        # Add nodes
        for node in self.nodes:
            G.add_node(
                node['id'],
                name=node['name'],
                floor=node['floor'],
                x=node['x'],
                y=node['y'],
                z=node['z'],
                type=node.get('type', 'Room'),
                is_room=node.get('is_room', True)
            )
        
        # Add edges
        for edge in self.edges:
            G.add_edge(
                edge['from'],
                edge['to'],
                weight=edge['weight'],
                floor=edge.get('floor', 'unknown'),
                type=edge.get('type', 'corridor')
            )
        
        self.network = G
        print(f"    Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    
    def find_shortest_path(self, start_id, end_id):
        """
        Find the shortest path between two nodes
        
        Parameters:
        -----------
        start_id : str
            ID of the start node (room)
        end_id : str
            ID of the end node (room)
        
        Returns:
        --------
        dict : Path information
        """
        if self.network is None:
            self.build_networkx_graph()
        
        try:
            # Find shortest path
            path = nx.shortest_path(
                self.network,
                source=start_id,
                target=end_id,
                weight='weight'
            )
            
            # Calculate total distance
            total_distance = 0
            for i in range(len(path) - 1):
                total_distance += self.network[path[i]][path[i+1]]['weight']
            
            # Get node details
            path_details = []
            for node_id in path:
                node_data = self.network.nodes[node_id]
                path_details.append({
                    'id': node_id,
                    'name': node_data.get('name', node_id),
                    'floor': node_data.get('floor', 'unknown'),
                    'type': node_data.get('type', 'unknown'),
                    'x': node_data.get('x', 0),
                    'y': node_data.get('y', 0),
                    'z': node_data.get('z', 0),
                })
            
            return {
                'path': path,
                'path_details': path_details,
                'distance': total_distance,
                'steps': len(path) - 1,
                'start': path[0],
                'end': path[-1]
            }
        
        except nx.NetworkXNoPath:
            return {'error': 'No path found'}
        except nx.NodeNotFound as e:
            return {'error': str(e)}
    
    def get_all_room_names(self):
        """
        Get a list of all room names for the UI
        """
        room_names = []
        for node in self.nodes:
            if node.get('is_room', False):
                room_names.append(node['name'])
        return sorted(room_names)
    
    def export_to_json(self, output_dir="src/data/routing/"):
        """
        Export network to JSON for use in the web application
        
        Parameters:
        -----------
        output_dir : str
            Directory to save JSON files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare nodes for JSON
        nodes_json = []
        for node in self.nodes:
            nodes_json.append({
                'id': node['id'],
                'name': node['name'],
                'floor': node['floor'],
                'x': node['x'],
                'y': node['y'],
                'z': node['z'],
                'type': node.get('type', 'Room'),
                'is_room': node.get('is_room', True)
            })
        
        # Prepare edges for JSON
        edges_json = []
        for edge in self.edges:
            edges_json.append({
                'from': edge['from'],
                'to': edge['to'],
                'weight': edge['weight'],
                'floor': edge.get('floor', 'unknown'),
                'type': edge.get('type', 'corridor')
            })
        
        # Save to file
        network_data = {
            'nodes': nodes_json,
            'edges': edges_json
        }
        
        file_path = os.path.join(output_dir, "network_graph.json")
        with open(file_path, 'w') as f:
            json.dump(network_data, f, indent=2)
        
        print(f" Network exported to: {file_path}")
        return file_path
    
    def run(self):
        """
        Run the full network building pipeline
        """
        print("\n" + "=" * 50)
        print("  BUILDING ROUTING NETWORK")
        print("=" * 50)
        
        self.load_bim_data()
        self.create_network_nodes()
        self.create_network_edges()
        self.build_networkx_graph()
        
        # Export for web use
        self.export_to_json()
        
        # Print summary
        print("\n" + "=" * 50)
        print(" NETWORK SUMMARY")
        print("=" * 50)
        print(f" Nodes:  {len(self.nodes)}")
        print(f"Edges:  {len(self.edges)}")
        print(f" Rooms:  {len([n for n in self.nodes if n.get('is_room', False)])}")
        print(f" Stairs: {len([n for n in self.nodes if n.get('is_stair', False)])}")
        
        # Test path
        room_names = self.get_all_room_names()
        if len(room_names) >= 2:
            print("\n Test: Shortest path")
            result = self.find_shortest_path(
                self.nodes[0]['id'],
                self.nodes[-1]['id']
            )
            if 'error' not in result:
                print(f"   From: {result['start']}")
                print(f"   To:   {result['end']}")
                print(f"   Distance: {result['distance']:.1f} units")
                print(f"   Steps: {result['steps']}")
        
        print("\n Network building complete!")
        return self.network


def main():
    """
    Main function to run network building
    """
    builder = NetworkBuilder()
    builder.run()


if __name__ == "__main__":
    main()