from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class Room:
    """Room data model"""
    id: str
    name: str
    floor: str
    type: Optional[str] = None
    area: Optional[float] = None
    capacity: Optional[int] = None
    equipment: Optional[str] = None
    year_built: Optional[int] = None
    maintenance_status: Optional[str] = None
    risk_level: Optional[str] = None
    temperature: Optional[float] = None
    noise_db: Optional[int] = None
    lighting_lux: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    center_z: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'type': self.type,
            'area': self.area,
            'capacity': self.capacity,
            'equipment': self.equipment,
            'year_built': self.year_built,
            'maintenance_status': self.maintenance_status,
            'risk_level': self.risk_level,
            'temperature': self.temperature,
            'noise_db': self.noise_db,
            'lighting_lux': self.lighting_lux,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'center_z': self.center_z
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Room':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Door:
    """Door data model"""
    id: str
    name: str
    floor: str
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    status: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'width': self.width,
            'height': self.height,
            'material': self.material,
            'status': self.status
        }


@dataclass
class NetworkNode:
    """Network node for routing"""
    id: str
    name: str
    floor: str
    x: float
    y: float
    z: float
    node_type: str = 'room'
    is_room: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'type': self.node_type,
            'is_room': self.is_room
        }


@dataclass
class NetworkEdge:
    """Network edge for routing"""
    source: str
    target: str
    weight: float
    floor: str
    edge_type: str = 'corridor'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'weight': self.weight,
            'floor': self.floor,
            'type': self.edge_type
        }


@dataclass
class RouteResult:
    """Route result from routing engine"""
    path: List[str]
    path_details: List[Dict[str, Any]]
    distance: float
    steps: int
    start: str
    end: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'path_details': self.path_details,
            'distance': self.distance,
            'steps': self.steps,
            'start': self.start,
            'end': self.end
        }