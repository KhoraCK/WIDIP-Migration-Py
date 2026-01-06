-- ===========================================
-- WIBOT Database Initialization Script
-- ===========================================
-- Ce script est execute automatiquement au premier
-- lancement de PostgreSQL via docker-entrypoint-initdb.d

-- ===========================================
-- Extension UUID
-- ===========================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ===========================================
-- TABLE: users
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    user_id             SERIAL PRIMARY KEY,
    username            VARCHAR(100) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    email               VARCHAR(255),
    role                VARCHAR(50) DEFAULT 'user',
    accreditation_level VARCHAR(2) DEFAULT 'N1' CHECK (accreditation_level IN ('N0', 'N1', 'N2', 'N3', 'N4')),
    created_at          TIMESTAMP DEFAULT NOW(),
    is_active           BOOLEAN DEFAULT true
);

COMMENT ON TABLE users IS 'Utilisateurs WIBOT';
COMMENT ON COLUMN users.password_hash IS 'Hash bcrypt du mot de passe';
COMMENT ON COLUMN users.accreditation_level IS 'Niveau Safeguard: N0=Lecture, N1=Tech, N2=Senior, N3=Admin, N4=SuperAdmin';

-- Migration: Ajouter colonne accreditation_level si elle n existe pas (pour BDD existantes)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'accreditation_level') THEN
        ALTER TABLE users ADD COLUMN accreditation_level VARCHAR(2) DEFAULT 'N1' CHECK (accreditation_level IN ('N0', 'N1', 'N2', 'N3', 'N4'));
    END IF;
END $$;

-- ===========================================
-- TABLE: conversations
-- ===========================================
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    title            VARCHAR(255),
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE conversations IS 'Conversations chat WIBOT';

-- ===========================================
-- TABLE: messages
-- ===========================================
CREATE TABLE IF NOT EXISTS messages (
    message_id       SERIAL PRIMARY KEY,
    conversation_id  UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    user_id          INTEGER REFERENCES users(user_id),
    role             VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT NOT NULL,
    tokens           INTEGER DEFAULT 0,
    attachments      JSONB,
    -- Colonnes analytics (ajoutees pour supervision)
    mode             VARCHAR(20) DEFAULT 'flash',
    rag_used         BOOLEAN DEFAULT false,
    files_count      INTEGER DEFAULT 0,
    created_at       TIMESTAMP DEFAULT NOW()
);

-- Migration: Ajouter colonnes si elles n'existent pas (pour BDD existantes)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'mode') THEN
        ALTER TABLE messages ADD COLUMN mode VARCHAR(20) DEFAULT 'flash';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'rag_used') THEN
        ALTER TABLE messages ADD COLUMN rag_used BOOLEAN DEFAULT false;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'files_count') THEN
        ALTER TABLE messages ADD COLUMN files_count INTEGER DEFAULT 0;
    END IF;
END $$;

COMMENT ON TABLE messages IS 'Messages des conversations';
COMMENT ON COLUMN messages.role IS 'user ou assistant uniquement';
COMMENT ON COLUMN messages.attachments IS 'Metadonnees fichiers joints (optionnel)';
COMMENT ON COLUMN messages.mode IS 'Mode IA utilise: code, flash, redaction';
COMMENT ON COLUMN messages.rag_used IS 'Si le RAG a ete utilise pour cette reponse';
COMMENT ON COLUMN messages.files_count IS 'Nombre de fichiers joints au message';

-- ===========================================
-- TABLE: user_token_usage
-- ===========================================
CREATE TABLE IF NOT EXISTS user_token_usage (
    usage_id        SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    month           DATE NOT NULL,
    used_tokens     BIGINT DEFAULT 0,
    quota_tokens    BIGINT DEFAULT 50000,
    UNIQUE(user_id, month)
);

COMMENT ON TABLE user_token_usage IS 'Compteur tokens mensuel par utilisateur';

-- ===========================================
-- INDEX pour performances
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_conversations_user
    ON conversations(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_messages_user
    ON messages(user_id);

CREATE INDEX IF NOT EXISTS idx_token_usage_user_month
    ON user_token_usage(user_id, month);

-- ===========================================
-- TRIGGER: Auto-update updated_at
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_conversation_timestamp ON conversations;
CREATE TRIGGER update_conversation_timestamp
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- DONNEES DE TEST
-- ===========================================

-- User test: khora / test123
-- Mot de passe en clair pour simplifier (en prod, utiliser bcrypt)
INSERT INTO users (username, password_hash, email, role, accreditation_level)
VALUES (
    'khora',
    'test123',
    'khora@widip.fr',
    'admin',
    'N4'
) ON CONFLICT (username) DO UPDATE SET accreditation_level = 'N4';

-- User test supplementaire: test / test123
INSERT INTO users (username, password_hash, email, role, accreditation_level)
VALUES (
    'test',
    'test123',
    'test@widip.fr',
    'user',
    'N1'
) ON CONFLICT (username) DO UPDATE SET accreditation_level = 'N1';

-- Conversation de test
INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'Conversation de test',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 hour'
) ON CONFLICT (conversation_id) DO NOTHING;

-- Messages de test
INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'user',
    'Bonjour WIBOT !',
    10,
    NOW() - INTERVAL '2 days'
WHERE NOT EXISTS (
    SELECT 1 FROM messages WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000'
);

INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'assistant',
    'Bonjour ! Je suis WIBOT, l''assistant IA de WIDIP. Comment puis-je t''aider aujourd''hui ?',
    25,
    NOW() - INTERVAL '2 days' + INTERVAL '2 seconds'
WHERE EXISTS (
    SELECT 1 FROM messages
    WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000'
    AND role = 'user'
) AND NOT EXISTS (
    SELECT 1 FROM messages
    WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000'
    AND role = 'assistant'
);

INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'user',
    'Peux-tu m''expliquer comment fonctionne PostgreSQL ?',
    15,
    NOW() - INTERVAL '2 days' + INTERVAL '1 minute'
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000') = 2;

INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'assistant',
    E'PostgreSQL est un systeme de gestion de base de donnees relationnelle (SGBDR) open source tres puissant.\n\n**Caracteristiques principales :**\n- Support complet SQL\n- Transactions ACID\n- Extensions (comme pgcrypto pour le chiffrement)\n- Excellent pour les charges de travail complexes\n\nC''est ce qu''on utilise chez WIDIP pour stocker les donnees WIBOT !',
    95,
    NOW() - INTERVAL '2 days' + INTERVAL '1 minute 5 seconds'
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000') = 3;

INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'user',
    'Et comment faire un backup ?',
    8,
    NOW() - INTERVAL '1 day'
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000') = 4;

INSERT INTO messages (conversation_id, user_id, role, content, tokens, created_at)
SELECT
    '550e8400-e29b-41d4-a716-446655440000',
    1,
    'assistant',
    E'Pour faire un backup PostgreSQL, tu as plusieurs options :\n\n```bash\n# Backup complet (dump SQL)\npg_dump -U widip -d wibot > backup.sql\n\n# Backup compresse\npg_dump -U widip -d wibot | gzip > backup.sql.gz\n\n# Restauration\npsql -U widip -d wibot < backup.sql\n```\n\nPour les backups automatiques, on peut utiliser un cron job ou un workflow n8n !',
    120,
    NOW() - INTERVAL '1 day' + INTERVAL '3 seconds'
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = '550e8400-e29b-41d4-a716-446655440000') = 5;

-- Token usage test (12,450 tokens utilises sur 50,000)
INSERT INTO user_token_usage (user_id, month, used_tokens, quota_tokens)
VALUES (
    1,
    DATE_TRUNC('month', CURRENT_DATE),
    12450,
    50000
) ON CONFLICT (user_id, month) DO UPDATE SET used_tokens = 12450;

-- ===========================================
-- VERIFICATION
-- ===========================================
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'WIBOT Database initialized successfully!';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Users: %', (SELECT COUNT(*) FROM users);
    RAISE NOTICE 'Conversations: %', (SELECT COUNT(*) FROM conversations);
    RAISE NOTICE 'Messages: %', (SELECT COUNT(*) FROM messages);
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Test user: khora / test123';
    RAISE NOTICE '===========================================';
END $$;
