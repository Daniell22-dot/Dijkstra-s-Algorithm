"""
export_3dtiles.py
Convert BIM models to 3D Tiles format for CesiumJS
"""

import os
import json
import subprocess
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class TilesExporter:
    """
    Export 3D models to 3D Tiles format
    Supports IFC, OBJ, GLTF, and other formats
    """
    
    def __init__(self, input_file=None, output_dir="src/models/3dtiles/"):
        """
        Initialize the exporter
        
        Parameters:
        -----------
        input_file : str, optional
            Path to the input 3D model file
        output_dir : str
            Directory to save 3D Tiles
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.tileset_file = None
        
    def check_dependencies(self):
        """
        Check if required tools are installed
        """
        missing = []
        
        # Check for Python packages
        try:
            import py3dtiles
        except ImportError:
            missing.append("py3dtiles (pip install py3dtiles)")
        
        # Check for Cesium ion CLI
        try:
            import subprocess
            result = subprocess.run(['cesium-ion', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                missing.append("cesium-ion-cli (npm install -g @cesium/cesium-ion-cli)")
        except:
            missing.append("cesium-ion-cli (npm install -g @cesium/cesium-ion-cli)")
        
        if missing:
            print("⚠️  Missing dependencies:")
            for m in missing:
                print(f"   - {m}")
            print("\nTo install:")
            print("   pip install py3dtiles")
            print("   npm install -g @cesium/cesium-ion-cli")
            return False
        
        print("✅ All dependencies installed")
        return True
    
    def convert_ifc_to_3dtiles(self, ifc_path=None):
        """
        Convert IFC file to 3D Tiles
        
        Parameters:
        -----------
        ifc_path : str, optional
            Path to IFC file. If not provided, uses self.input_file
        """
        path = ifc_path or self.input_file
        if not path:
            raise ValueError("No IFC file path provided")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"IFC file not found: {path}")
        
        print(f"🔄 Converting IFC to 3D Tiles: {path}")
        
        # Option 1: Use Cesium ion CLI (recommended)
        try:
            return self._convert_with_cesium_ion(path)
        except:
            print(" Cesium ion CLI failed, trying alternative...")
            return self._convert_with_py3dtiles(path)
    
    def _convert_with_cesium_ion(self, ifc_path):
        """
        Use Cesium ion CLI to convert IFC to 3D Tiles
        """
        output_dir = os.path.join(self.output_dir, "tileset")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            'cesium-ion',
            'upload',
            ifc_path,
            '--source',
            '--name',
            os.path.basename(ifc_path).replace('.ifc', ''),
            '--output',
            output_dir
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  Converted using Cesium ion")
                self.tileset_file = os.path.join(output_dir, "tileset.json")
                return self.tileset_file
            else:
                print(f" Cesium ion conversion failed: {result.stderr}")
                return None
        except Exception as e:
            print(f" Error: {e}")
            return None
    
    def _convert_with_py3dtiles(self, ifc_path):
        """
        Use py3dtiles library to convert IFC to 3D Tiles
        """
        try:
            from py3dtiles import convert
            from py3dtiles.converters import IfcConverter
            
            output_dir = os.path.join(self.output_dir, "tileset")
            os.makedirs(output_dir, exist_ok=True)
            
            # Convert using py3dtiles
            converter = IfcConverter(ifc_path)
            tileset = converter.to_3dtiles()
            
            # Save tileset
            self.tileset_file = os.path.join(output_dir, "tileset.json")
            with open(self.tileset_file, 'w') as f:
                json.dump(tileset.to_dict(), f, indent=2)
            
            print(f" Converted using py3dtiles")
            return self.tileset_file
        except Exception as e:
            print(f" py3dtiles conversion failed: {e}")
            return None
    
    def convert_obj_to_3dtiles(self, obj_path=None):
        """
        Convert OBJ file to 3D Tiles
        
        Parameters:
        -----------
        obj_path : str, optional
            Path to OBJ file. If not provided, uses self.input_file
        """
        path = obj_path or self.input_file
        if not path:
            raise ValueError("No OBJ file path provided")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"OBJ file not found: {path}")
        
        print(f" Converting OBJ to 3D Tiles: {path}")
        
        # Use py3dtiles for OBJ conversion
        try:
            from py3dtiles import convert
            from py3dtiles.converters import ObjConverter
            
            output_dir = os.path.join(self.output_dir, "tileset")
            os.makedirs(output_dir, exist_ok=True)
            
            converter = ObjConverter(path)
            tileset = converter.to_3dtiles()
            
            self.tileset_file = os.path.join(output_dir, "tileset.json")
            with open(self.tileset_file, 'w') as f:
                json.dump(tileset.to_dict(), f, indent=2)
            
            print(f"    Converted OBJ to 3D Tiles")
            return self.tileset_file
        except Exception as e:
            print(f"     OBJ conversion failed: {e}")
            return None
    
    def convert_gltf_to_3dtiles(self, gltf_path=None):
        """
        Convert GLTF/GLB file to 3D Tiles
        
        Parameters:
        -----------
        gltf_path : str, optional
            Path to GLTF/GLB file. If not provided, uses self.input_file
        """
        path = gltf_path or self.input_file
        if not path:
            raise ValueError("No GLTF file path provided")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"GLTF file not found: {path}")
        
        print(f" Converting GLTF to 3D Tiles: {path}")
        
        # Use py3dtiles for GLTF conversion
        try:
            from py3dtiles import convert
            from py3dtiles.converters import GltfConverter
            
            output_dir = os.path.join(self.output_dir, "tileset")
            os.makedirs(output_dir, exist_ok=True)
            
            converter = GltfConverter(path)
            tileset = converter.to_3dtiles()
            
            self.tileset_file = os.path.join(output_dir, "tileset.json")
            with open(self.tileset_file, 'w') as f:
                json.dump(tileset.to_dict(), f, indent=2)
            
            print(f"    Converted GLTF to 3D Tiles")
            return self.tileset_file
        except Exception as e:
            print(f"     GLTF conversion failed: {e}")
            return None
    
    def create_sample_tileset(self):
        """
        Create a sample 3D Tileset for testing
        """
        print(" Creating sample 3D Tileset for testing...")
        
        output_dir = os.path.join(self.output_dir, "tileset")
        os.makedirs(output_dir, exist_ok=True)
        
        tileset = {
            "asset": {
                "version": "1.0",
                "generator": "DeKUT-Campus-Digital-Twin"
            },
            "geometricError": 100,
            "root": {
                "boundingVolume": {
                    "box": [0, 0, 0, 20, 0, 0, 0, 20, 0, 0, 0, 10]
                },
                "geometricError": 50,
                "refine": "ADD",
                "children": [
                    {
                        "boundingVolume": {
                            "box": [0, 0, 0, 10, 0, 0, 0, 10, 0, 0, 0, 5]
                        },
                        "geometricError": 0,
                        "content": {
                            "uri": "building.b3dm"
                        }
                    }
                ]
            }
        }
        
        self.tileset_file = os.path.join(output_dir, "tileset.json")
        with open(self.tileset_file, 'w') as f:
            json.dump(tileset, f, indent=2)
        
        print(f"    Sample tileset created: {self.tileset_file}")
        return self.tileset_file
    
    def get_tileset_url(self):
        """
        Get the URL for the tileset
        """
        if self.tileset_file:
            return self.tileset_file
        return None
    
    def generate_campus_geojson(self, output_dir="src/data/gis/"):
        """
        Generate GeoJSON for campus layers
        
        Parameters:
        -----------
        output_dir : str
            Directory to save GeoJSON
        """
        os.makedirs(output_dir, exist_ok=True)
        
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-0.39825, 36.96145],
                        [-0.39805, 36.96145],
                        [-0.39805, 36.96195],
                        [-0.39825, 36.96195],
                        [-0.39825, 36.96145]
                    ]]
                },
                "properties": {
                    "name": "SOE Building",
                    "type": "building",
                    "floors": 3,
                    "area": 1200
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-0.39830, 36.96120],
                        [-0.39820, 36.96135],
                        [-0.39810, 36.96150],
                        [-0.39800, 36.96170]
                    ]
                },
                "properties": {
                    "name": "Main Path",
                    "type": "path"
                }
            }
        ]
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        file_path = os.path.join(output_dir, "campus_layers.json")
        with open(file_path, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f" Campus GeoJSON saved: {file_path}")
        return file_path


def main():
    """
    Main function to run export
    """
    exporter = TilesExporter()
    
    print("\n" + "=" * 50)
    print("  3D TILES EXPORTER")
    print("=" * 50)
    
    # Check dependencies
    exporter.check_dependencies()
    
    # Try to convert IFC if exists
    ifc_path = "src/models/ifc/DeKUT_SOE_Building.ifc"
    if os.path.exists(ifc_path):
        exporter.convert_ifc_to_3dtiles(ifc_path)
    else:
        print("  No IFC file found. Creating sample tileset...")
        exporter.create_sample_tileset()
    
    # Generate campus GeoJSON
    exporter.generate_campus_geojson()
    
    print("\n Export complete!")
    print(f" Tileset: {exporter.get_tileset_url()}")


if __name__ == "__main__":
    main()