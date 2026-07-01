"""
Building API endpoints
"""

from flask import jsonify
from . import buildings_bp
from database import db


@buildings_bp.route('/', methods=['GET'])
def get_building_info():
    """Get general building information"""
    try:
        # Get room count
        room_count = db.execute_one("SELECT COUNT(*) FROM rooms")[0]
        
        # Get floor count
        floor_count = db.execute_one("SELECT COUNT(DISTINCT floor) FROM rooms")[0]
        
        # Get total area
        total_area = db.execute_one("SELECT COALESCE(SUM(area), 0) FROM rooms")[0]
        
        # Get room types
        types_query = """
            SELECT type, COUNT(*) as count
            FROM rooms
            WHERE type IS NOT NULL
            GROUP BY type
            ORDER BY count DESC
        """
        types = db.execute_query(types_query)
        
        return jsonify({
            'success': True,
            'data': {
                'name': 'School of Engineering',
                'floors': floor_count,
                'total_rooms': room_count,
                'total_area': total_area,
                'room_types': [dict(row) for row in types],
                'risk_summary': get_risk_summary()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_risk_summary():
    """Get risk level summary"""
    try:
        query = """
            SELECT 
                risk_level,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rooms), 1) as percentage
            FROM rooms
            WHERE risk_level IS NOT NULL
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level
                    WHEN 'Low' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'High' THEN 3
                END
        """
        rows = db.execute_query(query)
        return [dict(row) for row in rows]
    
    except:
        return []


@buildings_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Get building statistics"""
    try:
        stats = {}
        
        # Total rooms
        stats['total_rooms'] = db.execute_one("SELECT COUNT(*) FROM rooms")[0]
        
        # Average area
        stats['avg_area'] = db.execute_one("SELECT COALESCE(AVG(area), 0) FROM rooms")[0]
        
        # Average temperature
        stats['avg_temperature'] = db.execute_one("SELECT COALESCE(AVG(temperature), 0) FROM rooms")[0]
        
        # Rooms by floor
        floor_query = """
            SELECT floor, COUNT(*) as count
            FROM rooms
            GROUP BY floor
            ORDER BY floor
        """
        stats['rooms_by_floor'] = [dict(row) for row in db.execute_query(floor_query)]
        
        # Risk distribution
        stats['risk_distribution'] = get_risk_summary()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500