# PostgreSQL Database Setup

## Quick Setup

### 1. Install PostgreSQL

**Mac (with Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from https://www.postgresql.org/download/windows/

### 2. Create the Database

```bash
# Login to PostgreSQL (default user is 'postgres')
psql postgres

# Create the database
CREATE DATABASE whatsapp_bot;

# Exit
\q
```

### 3. Install Python Dependencies

```bash
pip install -r server/requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.local.example` to `.env.local` and set your database URL:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_bot
```

**Note:** Replace `postgres:postgres` with your actual username:password if different.

### 5. Start the Server

```bash
npm run dev:server
```

The server will automatically create the necessary tables on startup!

## Database Schema

The database has two simple tables:

### `users` table
- `id` (UUID, primary key)
- `phone_number` (unique WhatsApp number)
- `created_at` (timestamp)

### `messages` table
- `id` (UUID, primary key)
- `user_id` (foreign key to users)
- `content` (text or AI-generated description)
- `content_type` ('text', 'image', or 'video')
- `timestamp` (when the message was received)

## How It Works

1. **Text message arrives** → Stored directly in `messages` table
2. **Image arrives** → Gemini analyzes → Description stored as `<image>description</image>`
3. **Video arrives** → Gemini analyzes → Description stored as `<video>description</video>`

## Viewing Data

```bash
# Connect to database
psql whatsapp_bot

# View all users
SELECT * FROM users;

# View all messages
SELECT * FROM messages ORDER BY timestamp DESC;

# View messages for a specific user
SELECT u.phone_number, m.content, m.content_type, m.timestamp
FROM messages m
JOIN users u ON m.user_id = u.id
WHERE u.phone_number = 'whatsapp:+14155551234'
ORDER BY m.timestamp DESC;
```

## Troubleshooting

**Connection errors:**
- Make sure PostgreSQL is running: `brew services list` (Mac) or `sudo systemctl status postgresql` (Linux)
- Check your DATABASE_URL is correct in `.env.local`
- Default PostgreSQL port is 5432

**Permission errors:**
- You may need to set a password for the postgres user
- Or create a new user: `CREATE USER myuser WITH PASSWORD 'mypassword';`
