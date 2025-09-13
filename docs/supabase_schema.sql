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

-- Create indexes for better performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_notification_settings_user_id ON notification_settings(user_id);

-- Function to search documents by similarity
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(1536),
    user_id INTEGER,
    match_threshold FLOAT,
    match_count INTEGER
)
RETURNS TABLE (
    id INTEGER,
    title VARCHAR(500),
    content_text TEXT,
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
        d.content_text,
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
    query_embedding vector(1536),
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