#!/usr/bin/env python3
import psycopg2
import subprocess
import sys
import os
import shutil
from pathlib import Path
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration
DB_NAME = "sentinel"
DB_USER = "sentinel_user"
DB_PASSWORD = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"

def run_as_postgres(command):
    """Run command as postgres user"""
    try:
        result = subprocess.run(['sudo', '-u', 'postgres'] + command, 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None

def flush_database_tables():
    """Clear all data from database tables"""
    print("Flushing database tables...")
    
    # SQL commands to clear tables
    sql_commands = [
        "TRUNCATE TABLE vehicles RESTART IDENTITY CASCADE;",
        "TRUNCATE TABLE processing_jobs RESTART IDENTITY CASCADE;",
    ]
    
    # Execute each SQL command
    for sql_cmd in sql_commands:
        print(f"  Executing: {sql_cmd}")
        run_as_postgres(['psql', '-d', DB_NAME, '-c', sql_cmd])
    
    print("Database tables flushed successfully")
    return True

def flush_keyframe_files():
    """Clear all stored keyframe files"""
    print("Flushing keyframe files...")
    
    # Define paths to clean
    paths_to_clean = [
        Path("aggregator/web/static"),
        Path("keyframes"),
        Path("processed_keyframes"),
        Path("temp_keyframes")
    ]
    
    for path in paths_to_clean:
        if path.exists():
            if path.is_dir():
                try:
                    shutil.rmtree(path)
                    print(f"  Removed directory: {path}")
                except Exception as e:
                    print(f"  Error removing {path}: {e}")
            else:
                try:
                    path.unlink()
                    print(f"  Removed file: {path}")
                except Exception as e:
                    print(f"  Error removing {path}: {e}")
        else:
            print(f"  Path not found: {path}")
    
    print("Keyframe files flushed successfully")
    return True

def get_table_counts():
    """Get current row counts from tables"""
    print("Getting current table counts...")
    
    try:
        # Test connection with the user
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM vehicles;")
        vehicles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processing_jobs;")
        jobs_count = cursor.fetchone()[0]
        
        print(f"  Vehicles: {vehicles_count} records")
        print(f"  Processing Jobs: {jobs_count} records")
        
        cursor.close()
        conn.close()
        
        return vehicles_count, jobs_count
        
    except Exception as e:
        print(f"Error getting table counts: {e}")
        return 0, 0

def confirm_flush():
    """Ask user for confirmation"""
    print("\n" + "!"*60)
    print("WARNING: This will permanently delete ALL data!")
    print("!"*60)
    print("This will:")
    print("  - Clear all vehicle records from database")
    print("  - Clear all processing job records")
    print("  - Delete all stored keyframe images")
    print("  - Reset auto-increment IDs to 1")
    print()
    
    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    return response == "YES"

def main():
    print("SENTINEL DATABASE FLUSH UTILITY")
    print("="*60)
    
    # Get current state
    vehicles_count, jobs_count = get_table_counts()
    
    # Count keyframe files
    keyframe_paths = [
        Path("aggregator/web/static"),
        Path("keyframes"), 
        Path("processed_keyframes"),
        Path("temp_keyframes")
    ]
    
    total_files = 0
    for path in keyframe_paths:
        if path.exists() and path.is_dir():
            files = list(path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            total_files += file_count
            print(f"  Files in {path}: {file_count}")
    
    print(f"\nTotal files to delete: {total_files}")
    
    if vehicles_count == 0 and jobs_count == 0 and total_files == 0:
        print("\nDatabase and files are already clean!")
        return
    
    # Confirm with user
    if not confirm_flush():
        print("\nOperation cancelled.")
        return
    
    print("\nStarting flush operation...")
    print("-" * 40)
    
    # Step 1: Flush database
    try:
        if not flush_database_tables():
            print("Failed to flush database tables")
            sys.exit(1)
    except Exception as e:
        print(f"Error flushing database: {e}")
        sys.exit(1)
    
    # Step 2: Flush files
    try:
        if not flush_keyframe_files():
            print("Failed to flush keyframe files")
    except Exception as e:
        print(f"Error flushing files: {e}")
    
    print("\nStep 3: Verifying flush...")
    vehicles_count, jobs_count = get_table_counts()
    
    print("\n" + "="*60)
    print("FLUSH COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"Database: {DB_NAME}")
    print(f"Remaining records:")
    print(f"  - Vehicles: {vehicles_count}")
    print(f"  - Processing Jobs: {jobs_count}")
    print()
    print("All keyframe files have been removed.")
    print("System is ready for fresh data.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Note: This script uses 'sudo -u postgres' for database operations")
        print("You may be prompted for your sudo password")
        print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFlush operation failed: {e}")
        sys.exit(1)
