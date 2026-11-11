"""
Configuration settings for the Flask application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5433')
    DB_NAME = os.getenv('DB_NAME', 'dijk')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

    # Prefer a full DATABASE_URL (e.g. postgresql://user:pass@host:port/db)
    DATABASE_URL = os.getenv('DATABASE_URL') or (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # File paths (extracted data lives under src/data)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(PROJECT_ROOT, 'src', 'data')
    BIM_DATA_DIR = os.path.join(DATA_DIR, 'bim')
    ROUTING_DATA_DIR = os.path.join(DATA_DIR, 'routing')
    MODEL_DIR = os.path.join(PROJECT_ROOT, 'src', 'models')
    TILESET_DIR = os.path.join(MODEL_DIR, '3dtiles', 'tileset')
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
    
    # API settings
    API_PREFIX = '/api/v1'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}