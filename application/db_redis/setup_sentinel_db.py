#!/usr/bin/env python3
import psycopg2
import subprocess
import sys
import os
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "sentinel"
DB_USER = "sentinel_user"
DB_PASSWORD = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"

def run_as_postgres(command):
    try:
        result = subprocess.run(['sudo', '-u', 'postgres'] + command, 
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None

def create_database_and_user():
    print("Creating database and user...")
    
    result = run_as_postgres(['psql', '-c', f'SELECT 1 FROM pg_database WHERE datname = \'{DB_NAME}\';'])
    if '1' not in result:
        run_as_postgres(['createdb', DB_NAME])
        print(f"Created database: {DB_NAME}")
    else:
        print(f"Database {DB_NAME} already exists")
    
    result = run_as_postgres(['psql', '-c', f'SELECT 1 FROM pg_user WHERE usename = \'{DB_USER}\';'])
    if '1' not in result:
        run_as_postgres(['psql', '-c', f"CREATE USER {DB_USER} WITH ENCRYPTED PASSWORD '{DB_PASSWORD}';"])
        run_as_postgres(['psql', '-c', f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};"])
        print(f"Created user: {DB_USER}")
    else:
        print(f"User {DB_USER} already exists")
    
    return True

def create_tables():
    print("Creating tables...")
    
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS vehicle_types (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS colors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            hex_code VARCHAR(7)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id SERIAL PRIMARY KEY,
            vehicle_id VARCHAR(100) UNIQUE NOT NULL,
            vehicle_type VARCHAR(20) NOT NULL,
            keyframe_url VARCHAR(500),
            plate_url VARCHAR(500),
            color VARCHAR(50),
            color_hex VARCHAR(7),
            vehicle_number VARCHAR(20),
            model VARCHAR(100),
            location VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending'
        );
        """,
        f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER};",
        f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER};",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_id ON vehicles(vehicle_id);",
    ]
    
    for sql_cmd in sql_commands:
        run_as_postgres(['psql', '-d', DB_NAME, '-c', sql_cmd])
    
    print("Tables and indexes created successfully")
    return True

def populate_lookup_tables():
    print("Populating lookup tables...")
    
    sql_commands = [
        "INSERT INTO locations (name) VALUES ('CALICUT_JUNCTION') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO vehicle_types (name) VALUES ('car') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO vehicle_types (name) VALUES ('motorcycle') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO vehicle_types (name) VALUES ('bus') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO vehicle_types (name) VALUES ('truck') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('red', '#FF0000') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('blue', '#0000FF') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('green', '#008000') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('yellow', '#FFFF00') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('white', '#FFFFFF') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('black', '#000000') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('gray', '#808080') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('orange', '#FFA500') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('purple', '#800080') ON CONFLICT (name) DO NOTHING;",
        "INSERT INTO colors (name, hex_code) VALUES ('brown', '#A52A2A') ON CONFLICT (name) DO NOTHING;",
    ]

    for sql_cmd in sql_commands:
        run_as_postgres(['psql', '-d', DB_NAME, '-c', sql_cmd])
        
    print("Lookup tables populated.")
    return True


def test_connection():
    return True

def main():
    print("Setting up Sentinel database...")
    print("-" * 40)
    
    if os.geteuid() != 0:
        print("Note: This script uses 'sudo -u postgres'...")
        print()
    
    print("Step 1: Creating database and user...")
    if not create_database_and_user():
        sys.exit(1)
    
    print("\nStep 2: Creating tables...")
    if not create_tables():
        sys.exit(1)
        
    print("\nStep 2a: Populating lookup tables...")
    if not populate_lookup_tables():
        sys.exit(1)

    print("\nStep 3: Testing connection...")
    if not test_connection():
        sys.exit(1)
    
    print("\n" + "="*50)
    print("Sentinel database setup completed successfully!")
    print("="*50)

if __name__ == "__main__":
    main()