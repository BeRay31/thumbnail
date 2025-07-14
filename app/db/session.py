import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        from app.db.models import job
        from app.db.base import Base
        
        with engine.connect() as conn:
            logger.info("Database connection successful")
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if "jobs" not in existing_tables:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created")
        else:
            logger.info("Database tables already exist")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()