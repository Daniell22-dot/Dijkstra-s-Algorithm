"""
Database connection and utility functions
"""

import psycopg2
import psycopg2.extras
from psycopg2 import pool
import json
import os
from contextlib import contextmanager
from config import Config


class Database:
    """Database connection manager using connection pooling"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the connection pool"""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            print(" Database connection pool created successfully")
        except Exception as e:
            print(f" Failed to create database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=psycopg2.extras.RealDictCursor):
        """Get a cursor from the connection"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur
                conn.commit()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.get_cursor() as cur:
            cur.execute(query, params or ())
            if cur.description:
                return cur.fetchall()
            return None
    
    def execute_one(self, query, params=None):
        """Execute a query and return one result"""
        with self.get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()
    
    def execute_insert(self, query, params=None):
        """Execute an insert query and return the inserted ID"""
        with self.get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()[0] if cur.description else None
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            print(" All database connections closed")


# Create a singleton instance
db = Database()


def initialize_database():
    """Create tables if they don't exist"""
    
    sql = """
    -- Rooms table
    CREATE TABLE IF NOT EXISTS rooms (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        floor VARCHAR(20) NOT NULL,
        type VARCHAR(50),
        area NUMERIC(10, 2),
        capacity INTEGER,
        equipment TEXT,
        year_built INTEGER,
        maintenance_status VARCHAR(20),
        risk_level VARCHAR(20),
        temperature NUMERIC(5, 2),
        noise_db INTEGER,
        lighting_lux INTEGER,
        latitude NUMERIC(10, 7),
        longitude NUMERIC(10, 7),
        center_x NUMERIC(10, 2),
        center_y NUMERIC(10, 2),
        center_z NUMERIC(10, 2)
    );

    -- Doors table
    CREATE TABLE IF NOT EXISTS doors (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        floor VARCHAR(20) NOT NULL,
        width NUMERIC(5, 2),
        height NUMERIC(5, 2),
        material VARCHAR(50),
        status VARCHAR(20)
    );

    -- Windows table
    CREATE TABLE IF NOT EXISTS windows (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        floor VARCHAR(20) NOT NULL,
        width NUMERIC(5, 2),
        height NUMERIC(5, 2),
        material VARCHAR(50),
        status VARCHAR(20)
    );

    -- Floors table
    CREATE TABLE IF NOT EXISTS floors (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        level INTEGER NOT NULL,
        area NUMERIC(10, 2),
        material VARCHAR(50),
        status VARCHAR(20)
    );

    -- Network nodes (for routing)
    CREATE TABLE IF NOT EXISTS network_nodes (
        id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        floor VARCHAR(20) NOT NULL,
        x NUMERIC(10, 2),
        y NUMERIC(10, 2),
        z NUMERIC(10, 2),
        node_type VARCHAR(20),
        is_room BOOLEAN DEFAULT TRUE
    );

    -- Network edges (for routing)
    CREATE TABLE IF NOT EXISTS network_edges (
        id SERIAL PRIMARY KEY,
        source VARCHAR(20) REFERENCES network_nodes(id),
        target VARCHAR(20) REFERENCES network_nodes(id),
        weight NUMERIC(10, 2),
        floor VARCHAR(20),
        edge_type VARCHAR(20)
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor);
    CREATE INDEX IF NOT EXISTS idx_doors_floor ON doors(floor);
    CREATE INDEX IF NOT EXISTS idx_windows_floor ON windows(floor);
    CREATE INDEX IF NOT EXISTS idx_network_nodes_floor ON network_nodes(floor);
    
    -- Enable pgRouting extension if available
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS pgrouting;
    """
    
    try:
        db.execute_query(sql)
        print(" Database tables created successfully")
    except Exception as e:
        print(f" Warning: {e}")
        print("   Some tables may already exist or pgRouting may not be installed")


if __name__ == "__main__":
    initialize_database()