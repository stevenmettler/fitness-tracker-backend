from src.database.database import Base, engine

def drop_all_tables():
    """Drop all tables"""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")

def create_all_tables():
    """Create all tables"""
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created!")

if __name__ == "__main__":
    # Drop all existing tables
    drop_all_tables()
    
    # Create all tables with new structure
    create_all_tables()
    
    print("Database reset complete!")