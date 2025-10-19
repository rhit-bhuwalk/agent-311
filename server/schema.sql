-- PostgreSQL schema for WhatsApp bot message storage
-- This file is for reference - SQLAlchemy will create these tables automatically

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,  -- 'text', 'image', 'video'
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_messages_user_id ON messages(user_id, timestamp DESC);
