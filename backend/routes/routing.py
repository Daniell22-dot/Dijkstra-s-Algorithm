"""
Routing API endpoints
"""

from flask import jsonify, request
from . import routing_bp
from database import db
from services.routing_engine import RoutingEngine
import psycopg2.extras


@routing_bp.route('/path/<start_id>/<end_id>', methods=['GET'])
def get_shortest_path(start_id, end_id):
    """Get the shortest path between two rooms"""
    try:
        # Initialize routing engine
        engine = RoutingEngine()
        
        # Find path
        result = engine.find_shortest_path(start_id, end_id)
        
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@routing_bp.route('/rooms', methods=['GET'])
def get_routing_rooms():
    """Get all rooms available for routing"""
    try:
        query = """
            SELECT id, name, floor, x, y, z
            FROM network_nodes
            WHERE is_room = TRUE
            ORDER BY floor, name
        """
        rows = db.execute_query(query)
        
        rooms = []
        for row in rows:
            rooms.append({
                'id': row['id'],
                'name': row['name'],
                'floor': row['floor'],
                'x': row['x'],
                'y': row['y'],
                'z': row['z']
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


@routing_bp.route('/network', methods=['GET'])
def get_network():
    """Get the complete network graph"""
    try:
        # Get nodes
        nodes_query = """
            SELECT id, name, floor, x, y, z, node_type, is_room
            FROM network_nodes
            ORDER BY floor, name
        """
        nodes = db.execute_query(nodes_query)
        
        # Get edges
        edges_query = """
            SELECT source, target, weight, floor, edge_type
            FROM network_edges
        """
        edges = db.execute_query(edges_query)
        
        return jsonify({
            'success': True,
            'data': {
                'nodes': [dict(row) for row in nodes],
                'edges': [dict(row) for row in edges]
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@routing_bp.route('/validate', methods=['POST'])
def validate_rooms():
    """Validate if rooms exist and are connected"""
    data = request.get_json()
    
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({
            'success': False,
            'error': 'start and end room IDs are required'
        }), 400
    
    start_id = data['start']
    end_id = data['end']
    
    try:
        engine = RoutingEngine()
        result = engine.validate_rooms(start_id, end_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@routing_bp.route('/distance/<start_id>/<end_id>', methods=['GET'])
def get_distance(start_id, end_id):
    """Get the shortest distance between two rooms"""
    try:
        engine = RoutingEngine()
        result = engine.find_shortest_path(start_id, end_id)
        
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'start': start_id,
                'end': end_id,
                'distance': result['distance'],
                'steps': result['steps']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500