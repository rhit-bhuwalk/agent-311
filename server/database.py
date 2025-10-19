"""PostgreSQL database connection and models."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey, text, select
from datetime import datetime
from typing import Optional
import os
from uuid import UUID, uuid4


# Database URL from environment or default to local PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_bot"
)

# Ensure we use asyncpg driver (Railway might provide postgresql:// format)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model - represents a WhatsApp user."""
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    phone_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()")
    )

    # Relationship
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Message(Base):
    """Message model - represents a WhatsApp message."""
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_from_user: Mapped[bool] = mapped_column(default=True, nullable=False)
    image_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Base64 encoded image
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()")
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="messages")


async def init_db():
    """Initialize database - create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


async def get_recent_messages(db: AsyncSession, user_id: UUID, limit: int = 10) -> list[Message]:
    """
    Get recent messages for a user in chronological order (oldest first).

    Args:
        db: Database session
        user_id: User ID
        limit: Number of messages to retrieve (default 10)

    Returns:
        List of Message objects in chronological order
    """
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    # Reverse to get chronological order (oldest first)
    messages.reverse()
    return messages
