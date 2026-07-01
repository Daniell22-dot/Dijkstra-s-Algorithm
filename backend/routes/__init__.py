"""
Route blueprints initialization
"""

from flask import Blueprint

# Create blueprints
rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/v1/rooms')
routing_bp = Blueprint('routing', __name__, url_prefix='/api/v1/routing')
buildings_bp = Blueprint('buildings', __name__, url_prefix='/api/v1/buildings')

# Import routes (this will register them)
from . import rooms, routing, buildings