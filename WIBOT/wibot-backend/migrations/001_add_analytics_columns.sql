-- ===========================================
-- Migration: Ajouter colonnes analytics à messages
-- ===========================================
-- Exécuter ce script manuellement sur une BDD existante:
-- docker exec -i wibot-postgres psql -U widip -d wibot < migrations/001_add_analytics_columns.sql

-- Ajouter colonne mode (code, flash, redaction)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'flash';

-- Ajouter colonne rag_used (si RAG utilisé pour la réponse)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS rag_used BOOLEAN DEFAULT false;

-- Ajouter colonne files_count (nombre de fichiers joints)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS files_count INTEGER DEFAULT 0;

-- Index pour requêtes analytics
CREATE INDEX IF NOT EXISTS idx_messages_mode ON messages(mode);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_analytics ON messages(user_id, mode, created_at);

-- Vérification
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully!';
    RAISE NOTICE 'Added columns: mode, rag_used, files_count to messages table';
END $$;
