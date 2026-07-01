"""
Process BIM data from ArchiCAD/IFC format
Extracts building elements: rooms, doors, windows, floors
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import ifcopenshell
from ifcopenshell import geom
from shapely.geometry import Polygon, Point, MultiPolygon
import warnings
warnings.filterwarnings('ignore')


class BIMProcessor:
    """
    Process IFC files from ArchiCAD to extract building data
    """
    
    def __init__(self, ifc_file_path=None):
        """
        Initialize the BIM processor
        
        Parameters:
        -----------
        ifc_file_path : str, optional
            Path to the IFC file from ArchiCAD
        """
        self.ifc_file_path = ifc_file_path
        self.ifc_file = None
        self.building_data = {
            'rooms': [],
            'doors': [],
            'windows': [],
            'floors': [],
            'walls': [],
            'spaces': []
        }
        self.settings = geom.settings()
        self.settings.set(geom.SETTINGS_USE_WORLD_COORDS, True)
        
    def load_ifc(self, file_path=None):
        """
        Load IFC file
        
        Parameters:
        -----------
        file_path : str, optional
            Path to IFC file. If not provided, uses self.ifc_file_path
        """
        path = file_path or self.ifc_file_path
        if not path:
            raise ValueError("No IFC file path provided")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"IFC file not found: {path}")
        
        print(f" Loading IFC file: {path}")
        self.ifc_file = ifcopenshell.open(path)
        print(f" IFC loaded successfully")
        print(f"   Project: {self.get_project_name()}")
        print(f"   Total elements: {len(self.ifc_file.by_type('IfcProduct'))}")
        
        return self.ifc_file
    
    def get_project_name(self):
        """Get the project name from IFC file"""
        project = self.ifc_file.by_type('IfcProject')
        if project:
            return project[0].Name
        return "Unknown Project"
    
    def extract_rooms(self):
        """
        Extract room/space information from IFC
        Returns: DataFrame with room data
        """
        print(" Extracting rooms...")
        rooms = []
        
        # Get all spaces (rooms)
        spaces = self.ifc_file.by_type('IfcSpace')
        
        for i, space in enumerate(spaces):
            try:
                room_data = {
                    'id': space.GlobalId,
                    'name': space.Name or f"Room_{i+1}",
                    'long_name': space.LongName or '',
                    'floor': self._get_floor_level(space),
                    'area': self._get_space_area(space),
                    'volume': self._get_space_volume(space),
                    'height': self._get_space_height(space),
                    'type': self._get_space_type(space),
                    'center_x': 0,
                    'center_y': 0,
                    'center_z': 0,
                    'properties': self._get_psets(space)
                }
                rooms.append(room_data)
            except Exception as e:
                print(f"    Error processing room {i+1}: {e}")
                continue
        
        print(f"    Extracted {len(rooms)} rooms")
        return pd.DataFrame(rooms)
    
    def extract_doors(self):
        """
        Extract door information from IFC
        Returns: DataFrame with door data
        """
        print(" Extracting doors...")
        doors = []
        
        door_elements = self.ifc_file.by_type('IfcDoor')
        
        for i, door in enumerate(door_elements):
            try:
                door_data = {
                    'id': door.GlobalId,
                    'name': door.Name or f"Door_{i+1}",
                    'width': self._get_door_width(door),
                    'height': self._get_door_height(door),
                    'floor': self._get_floor_level(door),
                    'material': self._get_material(door),
                    'type': 'Door',
                    'properties': self._get_psets(door)
                }
                doors.append(door_data)
            except Exception as e:
                print(f"    Error processing door {i+1}: {e}")
                continue
        
        print(f"    Extracted {len(doors)} doors")
        return pd.DataFrame(doors)
    
    def extract_windows(self):
        """
        Extract window information from IFC
        Returns: DataFrame with window data
        """
        print("🪟 Extracting windows...")
        windows = []
        
        window_elements = self.ifc_file.by_type('IfcWindow')
        
        for i, window in enumerate(window_elements):
            try:
                window_data = {
                    'id': window.GlobalId,
                    'name': window.Name or f"Window_{i+1}",
                    'width': self._get_door_width(window),
                    'height': self._get_door_height(window),
                    'floor': self._get_floor_level(window),
                    'material': self._get_material(window),
                    'type': 'Window',
                    'properties': self._get_psets(window)
                }
                windows.append(window_data)
            except Exception as e:
                print(f"    Error processing window {i+1}: {e}")
                continue
        
        print(f"    Extracted {len(windows)} windows")
        return pd.DataFrame(windows)
    
    def extract_floors(self):
        """
        Extract floor slab information from IFC
        Returns: DataFrame with floor data
        """
        print(" Extracting floors...")
        floors = []
        
        floor_elements = self.ifc_file.by_type('IfcSlab')
        
        for i, floor in enumerate(floor_elements):
            try:
                floor_data = {
                    'id': floor.GlobalId,
                    'name': floor.Name or f"Floor_{i+1}",
                    'level': self._get_floor_level(floor),
                    'type': 'Slab',
                    'properties': self._get_psets(floor)
                }
                floors.append(floor_data)
            except Exception as e:
                print(f"   Error processing floor {i+1}: {e}")
                continue
        
        print(f" Extracted {len(floors)} floors")
        return pd.DataFrame(floors)
    
    def extract_building_elements(self):
        """
        Extract all building elements from IFC
        """
        print("=" * 50)
        print("  EXTRACTING BUILDING ELEMENTS")
        print("=" * 50)
        
        # Extract all elements
        self.building_data['rooms'] = self.extract_rooms()
        self.building_data['doors'] = self.extract_doors()
        self.building_data['windows'] = self.extract_windows()
        self.building_data['floors'] = self.extract_floors()
        
        self._print_summary()
        
        return self.building_data
    
    def _get_floor_level(self, element):
        """Get the floor level of an element"""
        try:
            containment = self.ifc_file.get_inverse(element)
            for rel in containment:
                if rel.is_a('IfcRelContainedInSpatialStructure'):
                    container = rel.RelatingStructure
                    if container.is_a('IfcBuildingStorey'):
                        return container.Name or "0"
            return "0"
        except:
            return "0"
    
    def _get_space_area(self, space):
        """Get area of a space"""
        try:
            for rel in space.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            if prop.Name == 'GrossArea':
                                return prop.NominalValue.wrappedValue
            return None
        except:
            return None
    
    def _get_space_volume(self, space):
        """Get volume of a space"""
        try:
            for rel in space.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            if prop.Name == 'Volume':
                                return prop.NominalValue.wrappedValue
            return None
        except:
            return None
    
    def _get_space_height(self, space):
        """Get height of a space"""
        try:
            for rel in space.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            if prop.Name == 'Height':
                                return prop.NominalValue.wrappedValue
            return None
        except:
            return None
    
    def _get_door_width(self, element):
        """Get width of a door or window"""
        try:
            # Try to get from properties
            for rel in element.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            if prop.Name == 'Width':
                                return prop.NominalValue.wrappedValue
            return None
        except:
            return None
    
    def _get_door_height(self, element):
        """Get height of a door or window"""
        try:
            for rel in element.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            if prop.Name == 'Height':
                                return prop.NominalValue.wrappedValue
            return None
        except:
            return None
    
    def _get_material(self, element):
        """Get material of an element"""
        try:
            # Try to get from materials
            if element.HasAssociations:
                for rel in element.HasAssociations:
                    if rel.is_a('IfcRelAssociatesMaterial'):
                        material = rel.RelatingMaterial
                        if material.is_a('IfcMaterial'):
                            return material.Name
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_space_type(self, space):
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
            elif 'library' in name:
                return 'Library'
            elif 'toilet' in name or 'restroom' in name:
                return 'Restroom'
            elif 'corridor' in name or 'hall' in name:
                return 'Corridor'
            else:
                return 'Space'
        except:
            return 'Space'
    
    def _get_psets(self, element):
        """Extract all property sets from an element"""
        properties = {}
        try:
            for rel in element.IsDefinedBy:
                if rel.is_a('IfcRelDefinesByProperties'):
                    pset = rel.RelatingPropertyDefinition
                    if pset.is_a('IfcPropertySet'):
                        for prop in pset.HasProperties:
                            try:
                                value = prop.NominalValue.wrappedValue
                                if prop.Name:
                                    properties[prop.Name] = str(value)
                            except:
                                pass
        except:
            pass
        return properties
    
    def _print_summary(self):
        """Print a summary of extracted data"""
        print("\n" + "=" * 50)
        print(" EXTRACTION SUMMARY")
        print("=" * 50)
        print(f" Rooms:         {len(self.building_data['rooms'])}")
        print(f" Doors:         {len(self.building_data['doors'])}")
        print(f" Windows:       {len(self.building_data['windows'])}")
        print(f" Floors/Slabs:  {len(self.building_data['floors'])}")
        print("=" * 50)
    
    def save_to_csv(self, output_dir="src/data/bim/"):
        """
        Save extracted data to CSV files
        
        Parameters:
        -----------
        output_dir : str
            Directory to save CSV files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for key, df in self.building_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                file_path = os.path.join(output_dir, f"{key}.csv")
                df.to_csv(file_path, index=False)
                print(f" Saved: {file_path}")
        
        print(f"\n All data saved to: {output_dir}")
    
    def save_to_json(self, output_dir="src/data/bim/"):
        """
        Save extracted data to JSON files
        
        Parameters:
        -----------
        output_dir : str
            Directory to save JSON files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert DataFrames to dict
        data_dict = {}
        for key, df in self.building_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Convert NaN values to None for JSON
                data_dict[key] = df.replace({np.nan: None}).to_dict('records')
        
        file_path = os.path.join(output_dir, "building_data.json")
        with open(file_path, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        
        print(f" Saved: {file_path}")
        return file_path


def main():
    """
    Main function to run BIM processing
    """
    
    IFC_FILE_PATH = "src/models/ifc/DeKUT_SOE_Building.ifc"
    

    if not os.path.exists(IFC_FILE_PATH):
        print("  IFC file not found. Creating sample data...")
        create_sample_data()
        return
    
    
    processor = BIMProcessor(IFC_FILE_PATH)
    processor.load_ifc()
    processor.extract_building_elements()
    processor.save_to_csv()
    processor.save_to_json()
    
    print("\n BIM processing complete!")


def create_sample_data():
    """
    Create sample building data for testing when no IFC is available
    """
    print(" Creating sample building data...")
    
    # Sample rooms
    rooms = pd.DataFrame([
        {'id': 'R101', 'name': 'Room 101', 'long_name': 'Lecture Hall A', 
         'floor': '1', 'area': 45, 'volume': 135, 'height': 3.0, 
         'type': 'Lecture Hall', 'center_x': 0, 'center_y': 0, 'center_z': 1.5},
        {'id': 'R102', 'name': 'Room 102', 'long_name': 'Computer Lab', 
         'floor': '1', 'area': 38, 'volume': 114, 'height': 3.0, 
         'type': 'Laboratory', 'center_x': 10, 'center_y': 0, 'center_z': 1.5},
        {'id': 'R103', 'name': 'Room 103', 'long_name': 'Workshop', 
         'floor': '1', 'area': 60, 'volume': 180, 'height': 3.0, 
         'type': 'Workshop', 'center_x': 20, 'center_y': 0, 'center_z': 1.5},
        {'id': 'R201', 'name': 'Room 201', 'long_name': 'Lecture Hall B', 
         'floor': '2', 'area': 45, 'volume': 135, 'height': 3.0, 
         'type': 'Lecture Hall', 'center_x': 0, 'center_y': 0, 'center_z': 4.5},
        {'id': 'R202', 'name': 'Room 202', 'long_name': 'Office', 
         'floor': '2', 'area': 18, 'volume': 54, 'height': 3.0, 
         'type': 'Office', 'center_x': 10, 'center_y': 0, 'center_z': 4.5},
        {'id': 'R203', 'name': 'Room 203', 'long_name': 'Conference Room', 
         'floor': '2', 'area': 30, 'volume': 90, 'height': 3.0, 
         'type': 'Conference Room', 'center_x': 20, 'center_y': 0, 'center_z': 4.5},
        {'id': 'R301', 'name': 'Room 301', 'long_name': 'Research Lab', 
         'floor': '3', 'area': 42, 'volume': 126, 'height': 3.0, 
         'type': 'Laboratory', 'center_x': 0, 'center_y': 0, 'center_z': 7.5},
        {'id': 'R302', 'name': 'Room 302', 'long_name': 'Design Studio', 
         'floor': '3', 'area': 35, 'volume': 105, 'height': 3.0, 
         'type': 'Studio', 'center_x': 10, 'center_y': 0, 'center_z': 7.5},
    ])
    
    doors = pd.DataFrame([
        {'id': 'D101', 'name': 'Main Entrance', 'width': 2.0, 'height': 2.5, 
         'floor': '0', 'material': 'Glass', 'type': 'Door'},
        {'id': 'D102', 'name': 'Side Entrance', 'width': 1.5, 'height': 2.5, 
         'floor': '0', 'material': 'Wood', 'type': 'Door'},
        {'id': 'D103', 'name': 'Room 101 Door', 'width': 1.2, 'height': 2.5, 
         'floor': '1', 'material': 'Wood', 'type': 'Door'},
        {'id': 'D104', 'name': 'Room 102 Door', 'width': 1.2, 'height': 2.5, 
         'floor': '1', 'material': 'Wood', 'type': 'Door'},
        {'id': 'D105', 'name': 'Room 201 Door', 'width': 1.2, 'height': 2.5, 
         'floor': '2', 'material': 'Wood', 'type': 'Door'},
    ])
    
    # Sample windows
    windows = pd.DataFrame([
        {'id': 'W101', 'name': 'Window 101', 'width': 1.5, 'height': 1.5, 
         'floor': '1', 'material': 'Glass', 'type': 'Window'},
        {'id': 'W102', 'name': 'Window 102', 'width': 1.5, 'height': 1.5, 
         'floor': '1', 'material': 'Glass', 'type': 'Window'},
        {'id': 'W201', 'name': 'Window 201', 'width': 1.5, 'height': 1.5, 
         'floor': '2', 'material': 'Glass', 'type': 'Window'},
        {'id': 'W301', 'name': 'Window 301', 'width': 1.5, 'height': 1.5, 
         'floor': '3', 'material': 'Glass', 'type': 'Window'},
    ])
    
    # Sample floors
    floors = pd.DataFrame([
        {'id': 'F0', 'name': 'Ground Floor', 'level': '0', 'type': 'Slab'},
        {'id': 'F1', 'name': 'First Floor', 'level': '1', 'type': 'Slab'},
        {'id': 'F2', 'name': 'Second Floor', 'level': '2', 'type': 'Slab'},
        {'id': 'F3', 'name': 'Third Floor', 'level': '3', 'type': 'Slab'},
    ])
    
    # Save sample data
    output_dir = "src/data/bim/"
    os.makedirs(output_dir, exist_ok=True)
    
    rooms.to_csv(os.path.join(output_dir, "rooms.csv"), index=False)
    doors.to_csv(os.path.join(output_dir, "doors.csv"), index=False)
    windows.to_csv(os.path.join(output_dir, "windows.csv"), index=False)
    floors.to_csv(os.path.join(output_dir, "floors.csv"), index=False)
    
    # Save combined JSON
    data_dict = {
        'rooms': rooms.replace({np.nan: None}).to_dict('records'),
        'doors': doors.replace({np.nan: None}).to_dict('records'),
        'windows': windows.replace({np.nan: None}).to_dict('records'),
        'floors': floors.replace({np.nan: None}).to_dict('records'),
    }
    
    with open(os.path.join(output_dir, "building_data.json"), 'w') as f:
        json.dump(data_dict, f, indent=2, default=str)
    
    print(" Sample data created in: src/data/bim/")
    print(f"   - rooms.csv ({len(rooms)} rooms)")
    print(f"   - doors.csv ({len(doors)} doors)")
    print(f"   - windows.csv ({len(windows)} windows)")
    print(f"   - floors.csv ({len(floors)} floors)")
    print(f"   - building_data.json")


if __name__ == "__main__":
    main()