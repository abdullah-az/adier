"""
Script to initialize database tables using migrations.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.core.config import get_settings
from app.core.database import init_db


async def main():
    settings = get_settings()
    logger.info(f"Initializing database: {settings.database_url}")
    
    try:
        await init_db()
        logger.success("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
