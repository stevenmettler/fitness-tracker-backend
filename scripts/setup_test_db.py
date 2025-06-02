#!/usr/bin/env python3
"""
Script to set up the test database
Run this before running tests for the first time
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def create_test_database():
    """Create the test database if it doesn't exist"""
    
    # Database connection details
    db_name = "fitness_tracker_test"
    
    # Try to connect to the default postgres database to create our test DB
    try:
        # Connect to default postgres database
        engine = create_engine("postgresql://localhost/postgres")
        
        with engine.connect() as connection:
            # Don't use a transaction for CREATE DATABASE
            connection.execute(text("COMMIT"))
            
            # Check if database exists
            result = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if result.fetchone():
                print(f"✅ Database '{db_name}' already exists")
            else:
                # Create the database
                connection.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✅ Created database '{db_name}'")
                
    except OperationalError as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("\nMake sure PostgreSQL is running and you have access to create databases.")
        print("You might need to:")
        print("1. Start PostgreSQL service")
        print("2. Create a user with database creation privileges")
        print("3. Update the connection string in this script")
        sys.exit(1)

def test_connection():
    """Test connection to the test database"""
    try:
        test_db_url = "postgresql://localhost/fitness_tracker_test"
        engine = create_engine(test_db_url)
        
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print(f"✅ Successfully connected to test database")
            
    except OperationalError as e:
        print(f"❌ Cannot connect to test database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Setting up test database...")
    create_test_database()
    test_connection()
    print("\n🎉 Test database setup complete!")
    print("\nYou can now run tests with: pytest")
    print("\nIf you need to reset the test database, just drop and recreate it:")
    print("  psql -c 'DROP DATABASE fitness_tracker_test;'")
    print("  python scripts/setup_test_db.py")