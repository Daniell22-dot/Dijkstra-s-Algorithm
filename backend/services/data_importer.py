"""
Import data from CSV/JSON to database
"""

import os
import json
import pandas as pd
from config import Config
from database import db
import psycopg2.extras


class DataImporter:
    """Import data from files to database"""
    
    def __init__(self):
        """Initialize the data importer"""
        self.bim_dir = Config.BIM_DATA_DIR
        self.routing_dir = Config.ROUTING_DATA_DIR
    
    def import_all(self):
        """Import all data"""
        print(" Importing all data...")
        
        self.import_rooms()
        self.import_doors()
        self.import_windows()
        self.import_floors()
        self.import_network()
        
        print(" All data imported successfully")
    
    def import_rooms(self):
        """Import rooms from CSV or JSON"""
        print("   Importing rooms...")
        
        # Try CSV first
        csv_path = os.path.join(self.bim_dir, 'rooms.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            self._import_rooms_from_df(df)
            return
        
        # Try JSON
        json_path = os.path.join(self.bim_dir, 'building_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                if 'rooms' in data:
                    df = pd.DataFrame(data['rooms'])
                    self._import_rooms_from_df(df)
                    return
        
        print("  No room data found")
    
    def _import_rooms_from_df(self, df):
        """Import rooms from DataFrame"""
        
        # Clear existing data
        db.execute_query("TRUNCATE rooms CASCADE")
        
        for _, row in df.iterrows():
            try:
                query = """
                    INSERT INTO rooms (
                        id, name, floor, type, area, capacity, equipment,
                        year_built, maintenance_status, risk_level,
                        temperature, noise_db, lighting_lux,
                        latitude, longitude, center_x, center_y, center_z
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    row.get('id'),
                    row.get('name'),
                    row.get('floor'),
                    row.get('type'),
                    row.get('area'),
                    row.get('capacity'),
                    row.get('equipment'),
                    row.get('year_built'),
                    row.get('maintenance_status', 'Good'),
                    row.get('risk_level', 'Low'),
                    row.get('temperature'),
                    row.get('noise_db'),
                    row.get('lighting_lux'),
                    row.get('latitude'),
                    row.get('longitude'),
                    row.get('center_x', 0),
                    row.get('center_y', 0),
                    row.get('center_z', 0)
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"  Error importing room {row.get('id')}: {e}")
        
        print(f"  Imported {len(df)} rooms")
    
    def import_doors(self):
        """Import doors from CSV"""
        csv_path = os.path.join(self.bim_dir, 'doors.csv')
        if not os.path.exists(csv_path):
            print("   No doors data found")
            return
        
        df = pd.read_csv(csv_path)
        db.execute_query("TRUNCATE doors CASCADE")
        
        for _, row in df.iterrows():
            try:
                query = """
                    INSERT INTO doors (id, name, floor, width, height, material, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    row.get('id'),
                    row.get('name'),
                    row.get('floor'),
                    row.get('width'),
                    row.get('height'),
                    row.get('material'),
                    row.get('status', 'Good')
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"   Error importing door {row.get('id')}: {e}")
        
        print(f"   Imported {len(df)} doors")
    
    def import_windows(self):
        """Import windows from CSV"""
        csv_path = os.path.join(self.bim_dir, 'windows.csv')
        if not os.path.exists(csv_path):
            print("    No windows data found")
            return
        
        df = pd.read_csv(csv_path)
        db.execute_query("TRUNCATE windows CASCADE")
        
        for _, row in df.iterrows():
            try:
                query = """
                    INSERT INTO windows (id, name, floor, width, height, material, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    row.get('id'),
                    row.get('name'),
                    row.get('floor'),
                    row.get('width'),
                    row.get('height'),
                    row.get('material'),
                    row.get('status', 'Good')
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"    Error importing window {row.get('id')}: {e}")
        
        print(f"    Imported {len(df)} windows")
    
    def import_floors(self):
        """Import floors from CSV"""
        csv_path = os.path.join(self.bim_dir, 'floors.csv')
        if not os.path.exists(csv_path):
            print("    No floors data found")
            return
        
        df = pd.read_csv(csv_path)
        db.execute_query("TRUNCATE floors CASCADE")
        
        for _, row in df.iterrows():
            try:
                query = """
                    INSERT INTO floors (id, name, level, area, material, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    row.get('id'),
                    row.get('name'),
                    row.get('level'),
                    row.get('area'),
                    row.get('material', 'Concrete'),
                    row.get('status', 'Good')
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"   Error importing floor {row.get('id')}: {e}")
        
        print(f"    Imported {len(df)} floors")
    
    def import_network(self):
        """Import network graph from JSON"""
        json_path = os.path.join(self.routing_dir, 'network_graph.json')
        if not os.path.exists(json_path):
            print("    No network data found")
            return
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        db.execute_query("TRUNCATE network_nodes CASCADE")
        db.execute_query("TRUNCATE network_edges CASCADE")
        
        # Import nodes
        for node in data.get('nodes', []):
            try:
                query = """
                    INSERT INTO network_nodes (id, name, floor, x, y, z, node_type, is_room)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    node.get('id'),
                    node.get('name'),
                    node.get('floor', '0'),
                    node.get('x', 0),
                    node.get('y', 0),
                    node.get('z', 0),
                    node.get('type', 'room'),
                    node.get('is_room', True)
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"   Error importing node {node.get('id')}: {e}")
        
        # Import edges
        for edge in data.get('edges', []):
            try:
                query = """
                    INSERT INTO network_edges (source, target, weight, floor, edge_type)
                    VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    edge.get('from'),
                    edge.get('to'),
                    edge.get('weight', 1),
                    edge.get('floor', 'unknown'),
                    edge.get('type', 'corridor')
                )
                db.execute_query(query, params)
            except Exception as e:
                print(f"  Error importing edge: {e}")
        
        print(f"  Imported {len(data.get('nodes', []))} nodes and {len(data.get('edges', []))} edges")