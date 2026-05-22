-- Pokemon Drafter Database Schema
-- All variable names in snake_case

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    team_color VARCHAR(10) NOT NULL CHECK (team_color IN ('RED', 'BLUE')),
    avatar_url VARCHAR(255),
    score INTEGER DEFAULT 0 CHECK (score >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    team_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    team_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team Pokemon relationship
CREATE TABLE IF NOT EXISTS team_pokemon (
    team_id INTEGER REFERENCES teams(team_id) ON DELETE CASCADE,
    pokemon_id INTEGER NOT NULL,
    position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 6),
    PRIMARY KEY (team_id, position)
);

-- Duels table
CREATE TABLE IF NOT EXISTS duels (
    duel_id SERIAL PRIMARY KEY,
    red_player_id INTEGER REFERENCES users(user_id),
    blue_player_id INTEGER REFERENCES users(user_id),
    red_team_id INTEGER REFERENCES teams(team_id),
    blue_team_id INTEGER REFERENCES teams(team_id),
    game_mode VARCHAR(20) NOT NULL CHECK (game_mode IN ('random', 'constructed', 'draft')),
    winner_id INTEGER REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'active', 'completed', 'forfeited')),
    current_turn INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT different_players CHECK (red_player_id != blue_player_id)
);

-- Duel turns history
CREATE TABLE IF NOT EXISTS duel_turns (
    turn_id SERIAL PRIMARY KEY,
    duel_id INTEGER REFERENCES duels(duel_id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    red_pokemon_id INTEGER,
    blue_pokemon_id INTEGER,
    red_action VARCHAR(20), -- 'switch' or 'stay'
    blue_action VARCHAR(20),
    red_advantage DECIMAL(5,2),
    blue_advantage DECIMAL(5,2),
    ko_pokemon_ids INTEGER[], -- Array of pokemon IDs that were KO'd
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    message_text TEXT NOT NULL,
    team_only BOOLEAN DEFAULT FALSE,
    duel_id INTEGER REFERENCES duels(duel_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pokemon cache (to reduce API calls)
CREATE TABLE IF NOT EXISTS pokemon_cache (
    pokemon_id INTEGER PRIMARY KEY,
    pokemon_name VARCHAR(100) NOT NULL,
    type_primary VARCHAR(20) NOT NULL,
    type_secondary VARCHAR(20),
    height INTEGER,
    weight INTEGER,
    base_stats JSONB,
    description TEXT,
    habitat VARCHAR(50),
    sprite_url VARCHAR(255),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs table (for admin)
CREATE TABLE IF NOT EXISTS system_logs (
    log_id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_team_color ON users(team_color);
CREATE INDEX idx_teams_user_id ON teams(user_id);
CREATE INDEX idx_duels_status ON duels(status);
CREATE INDEX idx_duels_players ON duels(red_player_id, blue_player_id);
CREATE INDEX idx_chat_messages_duel ON chat_messages(duel_id);
CREATE INDEX idx_system_logs_service ON system_logs(service_name, created_at);

-- Insert test users
INSERT INTO users (username, email, password_hash, first_name, last_name, team_color, score) VALUES
('red_player1', 'red1@pokemon.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XUuYdEUzNRai', 'Red', 'One', 'RED', 100),
('red_player2', 'red2@pokemon.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XUuYdEUzNRai', 'Red', 'Two', 'RED', 100),
('blue_player1', 'blue1@pokemon.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XUuYdEUzNRai', 'Blue', 'One', 'BLUE', 100),
('blue_player2', 'blue2@pokemon.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XUuYdEUzNRai', 'Blue', 'Two', 'BLUE', 100),
('admin', 'admin@pokemon.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XUuYdEUzNRai', 'Admin', 'User', 'RED', 0)
ON CONFLICT (email) DO NOTHING;

-- Insert some test teams
INSERT INTO teams (user_id, team_name) VALUES
(1, 'Fire Squad'),
(2, 'Electric Team'),
(3, 'Water Warriors'),
(4, 'Grass Masters')
ON CONFLICT DO NOTHING;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
