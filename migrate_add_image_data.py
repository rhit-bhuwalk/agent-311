"""Migration script to add image_data column to messages table."""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env.local
dotenv_path = Path(__file__).parent / '.env.local'
load_dotenv(dotenv_path=dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

# Convert to asyncpg format
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)


async def migrate():
    """Add image_data column to messages table."""
    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check if column already exists
        result = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'messages' AND column_name = 'image_data'
        """)

        if result:
            print("✅ image_data column already exists, skipping migration")
            return

        print("📝 Adding image_data column to messages table...")
        await conn.execute("""
            ALTER TABLE messages
            ADD COLUMN image_data TEXT NULL
        """)

        print("✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(migrate())
