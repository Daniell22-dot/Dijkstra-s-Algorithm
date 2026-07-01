from flask import Flask, jsonify
from flask_cors import CORS
from config import Config, config
from database import db, initialize_database
import os


def create_app(config_name='default'):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize database
    initialize_database()
    
    # Register blueprints
    from routes import rooms_bp, routing_bp, buildings_bp
    app.register_blueprint(rooms_bp)
    app.register_blueprint(routing_bp)
    app.register_blueprint(buildings_bp)
    
    # Health check endpoint
    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'DeKUT Campus Digital Twin API',
            'version': '1.0.0'
        })
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'service': 'DeKUT Campus Digital Twin API',
            'version': '1.0.0',
            'endpoints': {
                'rooms': '/api/v1/rooms',
                'room': '/api/v1/rooms/{id}',
                'routing': '/api/v1/routing/path/{start}/{end}',
                'buildings': '/api/v1/buildings',
                'health': '/api/v1/health'
            }
        })
    
    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )