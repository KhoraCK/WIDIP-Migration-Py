-- =============================================================================
-- Script d'initialisation PostgreSQL pour WIDIP Knowledge Base
-- Utilise pgvector pour la recherche vectorielle RAG
-- Version: 2.0 (e5-multilingual-large - 1024 dimensions)
-- =============================================================================

-- Activer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table de la base de connaissances
CREATE TABLE IF NOT EXISTS widip_knowledge_base (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    problem_summary TEXT NOT NULL,
    solution_summary TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    embedding vector(1024),  -- e5-multilingual-large génère des vecteurs de 1024 dimensions
    quality_score NUMERIC(3,2) DEFAULT 0.0,  -- Score de qualité 0.00-1.00
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- =============================================================================
-- Table SAFEGUARD - File d'attente des approbations L3
-- =============================================================================
CREATE TABLE IF NOT EXISTS safeguard_pending_approvals (
    id SERIAL PRIMARY KEY,
    approval_id VARCHAR(100) UNIQUE NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    security_level VARCHAR(10) NOT NULL,
    arguments JSONB DEFAULT '{}',
    requester_workflow VARCHAR(100),
    requester_ip VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, expired
    approver VARCHAR(100),
    approval_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    decided_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '1 hour')
);

CREATE INDEX IF NOT EXISTS idx_safeguard_status ON safeguard_pending_approvals (status);
CREATE INDEX IF NOT EXISTS idx_safeguard_approval_id ON safeguard_pending_approvals (approval_id);

-- =============================================================================
-- Table de logs d'audit SAFEGUARD
-- =============================================================================
CREATE TABLE IF NOT EXISTS safeguard_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    tool_name VARCHAR(100) NOT NULL,
    security_level VARCHAR(10) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- allowed, blocked, approved, rejected
    caller_ip VARCHAR(50),
    workflow_id VARCHAR(100),
    approval_id VARCHAR(100),
    details JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_safeguard_audit_timestamp ON safeguard_audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_safeguard_audit_tool ON safeguard_audit_log (tool_name);

-- Index pour la recherche vectorielle (HNSW pour les performances)
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
ON widip_knowledge_base
USING hnsw (embedding vector_cosine_ops);

-- Index pour les recherches par catégorie
CREATE INDEX IF NOT EXISTS idx_knowledge_category
ON widip_knowledge_base (category);

-- Index pour les recherches par ticket_id
CREATE INDEX IF NOT EXISTS idx_knowledge_ticket_id
ON widip_knowledge_base (ticket_id);

-- Index GIN pour les tags
CREATE INDEX IF NOT EXISTS idx_knowledge_tags
ON widip_knowledge_base USING gin (tags);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour updated_at
DROP TRIGGER IF EXISTS update_knowledge_updated_at ON widip_knowledge_base;
CREATE TRIGGER update_knowledge_updated_at
    BEFORE UPDATE ON widip_knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Données de test (optionnel)
-- INSERT INTO widip_knowledge_base (ticket_id, problem_summary, solution_summary, category, tags)
-- VALUES
--     ('TEST-001', 'VPN ne fonctionne pas après mise à jour Windows', 'Réinstaller le client VPN et redémarrer', 'VPN', ARRAY['vpn', 'windows', 'client']),
--     ('TEST-002', 'Impossible de se connecter à l''imprimante réseau', 'Supprimer et réajouter l''imprimante, vérifier le pilote', 'Imprimante', ARRAY['imprimante', 'réseau', 'pilote']);

-- =============================================================================
-- Table des logs d'incidents (traçabilité complète)
-- =============================================================================
CREATE TABLE IF NOT EXISTS incident_logs (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) NOT NULL,
    ticket_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,  -- detection, triage, diagnostic, action, resolution
    agent_name VARCHAR(50),  -- MONITOR, TRIAGE, SUPPORT, DIAG, etc.
    action_taken TEXT,
    result JSONB DEFAULT '{}',
    confidence_score NUMERIC(5,4),  -- 0.0000 - 1.0000
    human_validated BOOLEAN DEFAULT FALSE,
    validation_by VARCHAR(100),
    validation_at TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_incident_logs_incident_id ON incident_logs (incident_id);
CREATE INDEX IF NOT EXISTS idx_incident_logs_ticket_id ON incident_logs (ticket_id);
CREATE INDEX IF NOT EXISTS idx_incident_logs_timestamp ON incident_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_incident_logs_agent ON incident_logs (agent_name);
CREATE INDEX IF NOT EXISTS idx_incident_logs_event_type ON incident_logs (event_type);

-- =============================================================================
-- Table des logs d'activité des agents WIDIP
-- =============================================================================
CREATE TABLE IF NOT EXISTS widip_agent_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    agent_name VARCHAR(50) NOT NULL,  -- MONITOR, TRIAGE, SUPPORT, DIAG, ONBOARD, HR
    session_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    tool_called VARCHAR(100),
    security_level VARCHAR(10),
    input_summary TEXT,  -- Résumé (pas de données sensibles)
    output_summary TEXT,
    success BOOLEAN,
    error_message TEXT,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON widip_agent_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON widip_agent_logs (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON widip_agent_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_tool ON widip_agent_logs (tool_called);

COMMENT ON TABLE widip_knowledge_base IS 'Base de connaissances RAG pour les agents IA WIDIP';
COMMENT ON COLUMN widip_knowledge_base.embedding IS 'Vecteur embedding généré par e5-multilingual-large (1024 dim)';
COMMENT ON TABLE safeguard_pending_approvals IS 'File d''attente des actions L3 en attente de validation humaine';
COMMENT ON TABLE safeguard_audit_log IS 'Journal d''audit de toutes les actions SAFEGUARD';
COMMENT ON TABLE incident_logs IS 'Traçabilité complète des incidents traités par les agents WIDIP';
COMMENT ON TABLE widip_agent_logs IS 'Logs d''activité et métriques des agents IA WIDIP';
