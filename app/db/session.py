import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize database tables if they don't exist
    """
    try:
        # Import all models to ensure they are registered with Base
        from app.db.models import job  # Import the job model
        from app.db.base import Base
        
        # Test database connection first
        with engine.connect() as conn:
            logger.info("✅ Database connection successful")
        
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if "jobs" not in existing_tables:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully!")
        else:
            logger.info("✅ Database tables already exist")
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        logger.error("💡 Make sure PostgreSQL is running and connection details are correct")
        raise e

def get_db(): # DB Session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()