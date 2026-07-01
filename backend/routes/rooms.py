"""
Room API endpoints
"""

from flask import jsonify, request
from . import rooms_bp
from database import db
import psycopg2.extras


@rooms_bp.route('/', methods=['GET'])
def get_all_rooms():
    """Get all rooms"""
    try:
        query = """
            SELECT id, name, floor, type, area, capacity, equipment,
                   year_built, maintenance_status, risk_level, 
                   temperature, noise_db, lighting_lux,
                   latitude, longitude
            FROM rooms
            ORDER BY floor, name
        """
        rows = db.execute_query(query)
        
        rooms = []
        for row in rows:
            rooms.append({
                'id': row['id'],
                'name': row['name'],
                'floor': row['floor'],
                'type': row['type'],
                'area': row['area'],
                'capacity': row['capacity'],
                'equipment': row['equipment'],
                'year_built': row['year_built'],
                'maintenance_status': row['maintenance_status'],
                'risk_level': row['risk_level'],
                'temperature': row['temperature'],
                'noise_db': row['noise_db'],
                'lighting_lux': row['lighting_lux'],
                'latitude': row['latitude'],
                'longitude': row['longitude']
            })
        
        return jsonify({
            'success': True,
            'count': len(rooms),
            'data': rooms
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rooms_bp.route('/<room_id>', methods=['GET'])
def get_room(room_id):
    """Get a specific room by ID"""
    try:
        query = """
            SELECT id, name, floor, type, area, capacity, equipment,
                   year_built, maintenance_status, risk_level, 
                   temperature, noise_db, lighting_lux,
                   latitude, longitude, center_x, center_y, center_z
            FROM rooms
            WHERE id = %s
        """
        row = db.execute_one(query, (room_id,))
        
        if not row:
            return jsonify({
                'success': False,
                'error': f'Room {room_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': row['id'],
                'name': row['name'],
                'floor': row['floor'],
                'type': row['type'],
                'area': row['area'],
                'capacity': row['capacity'],
                'equipment': row['equipment'],
                'year_built': row['year_built'],
                'maintenance_status': row['maintenance_status'],
                'risk_level': row['risk_level'],
                'temperature': row['temperature'],
                'noise_db': row['noise_db'],
                'lighting_lux': row['lighting_lux'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'center_x': row['center_x'],
                'center_y': row['center_y'],
                'center_z': row['center_z']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rooms_bp.route('/floor/<floor_name>', methods=['GET'])
def get_rooms_by_floor(floor_name):
    """Get all rooms on a specific floor"""
    try:
        query = """
            SELECT id, name, floor, type, area, capacity, equipment,
                   year_built, maintenance_status, risk_level, 
                   temperature, noise_db, lighting_lux,
                   latitude, longitude
            FROM rooms
            WHERE floor = %s
            ORDER BY name
        """
        rows = db.execute_query(query, (floor_name,))
        
        rooms = []
        for row in rows:
            rooms.append({
                'id': row['id'],
                'name': row['name'],
                'floor': row['floor'],
                'type': row['type'],
                'area': row['area'],
                'capacity': row['capacity'],
                'equipment': row['equipment'],
                'year_built': row['year_built'],
                'maintenance_status': row['maintenance_status'],
                'risk_level': row['risk_level'],
                'temperature': row['temperature'],
                'noise_db': row['noise_db'],
                'lighting_lux': row['lighting_lux'],
                'latitude': row['latitude'],
                'longitude': row['longitude']
            })
        
        return jsonify({
            'success': True,
            'count': len(rooms),
            'data': rooms
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rooms_bp.route('/search', methods=['GET'])
def search_rooms():
    """Search rooms by name or type"""
    query_param = request.args.get('q', '')
    
    if not query_param:
        return jsonify({
            'success': False,
            'error': 'Search query parameter "q" is required'
        }), 400
    
    try:
        query = """
            SELECT id, name, floor, type, area, capacity
            FROM rooms
            WHERE name ILIKE %s OR type ILIKE %s
            ORDER BY floor, name
            LIMIT 20
        """
        search_pattern = f'%{query_param}%'
        rows = db.execute_query(query, (search_pattern, search_pattern))
        
        rooms = []
        for row in rows:
            rooms.append({
                'id': row['id'],
                'name': row['name'],
                'floor': row['floor'],
                'type': row['type'],
                'area': row['area'],
                'capacity': row['capacity']
            })
        
        return jsonify({
            'success': True,
            'count': len(rooms),
            'data': rooms
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rooms_bp.route('/floors', methods=['GET'])
def get_floors():
    """Get all floors with room counts"""
    try:
        query = """
            SELECT floor, COUNT(*) as room_count
            FROM rooms
            GROUP BY floor
            ORDER BY floor
        """
        rows = db.execute_query(query)
        
        floors = []
        for row in rows:
            floors.append({
                'name': row['floor'],
                'room_count': row['room_count']
            })
        
        return jsonify({
            'success': True,
            'data': floors
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500