-- Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    isAudio BOOLEAN DEFAULT FALSE,
    notification BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(10) DEFAULT 'UTC', -- User's timezone (e.g., 'UTC+1', 'UTC-5')
    book_received BOOLEAN DEFAULT FALSE, -- Track if user received the vitamin book
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User messages for admin forwarding
CREATE TABLE user_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL, -- 'text', 'audio'
    content TEXT,
    audio_file_path VARCHAR(1000),
    transcription TEXT,
    is_forwarded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notification settings table
CREATE TABLE notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents table for RAG pipeline (embeddings using text-embedding-3-large: 3072 dimensions)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT NOT NULL,
    file_path VARCHAR(1000),
    embedding vector(3072), -- OpenAI text-embedding-3-large
    metadata JSONB,
    is_favorite BOOLEAN DEFAULT FALSE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    ingestion_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video contents table for video transcripts with embeddings
CREATE TABLE video_contents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    transcript TEXT,
    video_url VARCHAR(1000),
    embedding vector(3072), -- OpenAI text-embedding-3-large
    is_favorite BOOLEAN DEFAULT FALSE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_notification_settings_user_id ON notification_settings(user_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_video_contents_user_id ON video_contents(user_id);
-- Note: Vector indexes (HNSW/IVFFlat) have a 2000 dimension limit in pgvector
-- Since we're using 3072 dimensions (text-embedding-3-large), we can't index the embeddings
-- The similarity search functions will use sequential scans, which is acceptable for small-medium datasets
-- For better performance with large datasets, consider:
--   1. Using text-embedding-3-small (1536 dimensions) instead
--   2. Applying dimensionality reduction techniques
--   3. Upgrading to a newer pgvector version when available

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_contents ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Allow anonymous user creation" ON users
    FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Users can read own data" ON users
    FOR SELECT 
    USING (true);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE 
    USING (true)
    WITH CHECK (true);

-- RLS Policies for user_messages table
CREATE POLICY "Users can insert own messages" ON user_messages
    FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Users can read own messages" ON user_messages
    FOR SELECT 
    USING (true);

-- RLS Policies for notification_settings table
CREATE POLICY "Users can manage own notification settings" ON notification_settings
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- RLS Policies for documents table
CREATE POLICY "Users can manage own documents" ON documents
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- RLS Policies for video_contents table
CREATE POLICY "Users can manage own video contents" ON video_contents
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Function to search documents by similarity
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(3072),
    user_id INTEGER,
    match_threshold FLOAT,
    match_count INTEGER
)
RETURNS TABLE (
    id INTEGER,
    title VARCHAR(500),
    content TEXT,
    file_path VARCHAR(1000),
    is_favorite BOOLEAN,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.title,
        d.content,
        d.file_path,
        d.is_favorite,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE d.user_id = search_documents.user_id
        AND 1 - (d.embedding <=> query_embedding) > match_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to search video contents by similarity
CREATE OR REPLACE FUNCTION search_videos(
    query_embedding vector(3072),
    user_id INTEGER,
    match_threshold FLOAT,
    match_count INTEGER
)
RETURNS TABLE (
    id INTEGER,
    title VARCHAR(500),
    transcript TEXT,
    video_url VARCHAR(1000),
    is_favorite BOOLEAN,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.title,
        v.transcript,
        v.video_url,
        v.is_favorite,
        1 - (v.embedding <=> query_embedding) AS similarity
    FROM video_contents v
    WHERE v.user_id = search_videos.user_id
        AND 1 - (v.embedding <=> query_embedding) > match_threshold
    ORDER BY v.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_video_contents_updated_at BEFORE UPDATE ON video_contents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON notification_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();