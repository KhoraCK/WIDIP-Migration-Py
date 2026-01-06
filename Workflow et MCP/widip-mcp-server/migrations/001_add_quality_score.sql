-- =============================================================================
-- Migration 001 : Ajout du score de qualité dans widip_knowledge_base
-- Date : 24 Décembre 2025
-- Auteur : Khora
-- =============================================================================

-- Ajouter la colonne quality_score si elle n'existe pas déjà
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='widip_knowledge_base'
        AND column_name='quality_score'
    ) THEN
        ALTER TABLE widip_knowledge_base
        ADD COLUMN quality_score NUMERIC(3,2) DEFAULT 0.0;

        RAISE NOTICE 'Colonne quality_score ajoutée avec succès';
    ELSE
        RAISE NOTICE 'Colonne quality_score existe déjà, migration ignorée';
    END IF;
END $$;

-- Créer un index pour améliorer les performances de recherche filtrée
CREATE INDEX IF NOT EXISTS idx_knowledge_quality_score
ON widip_knowledge_base (quality_score DESC)
WHERE quality_score >= 0.4;

-- Mettre à jour les entrées existantes avec un score par défaut de 0.5
-- (neutre, évite de filtrer l'existant)
UPDATE widip_knowledge_base
SET quality_score = 0.5
WHERE quality_score = 0.0 OR quality_score IS NULL;

-- Afficher les statistiques
DO $$
DECLARE
    total_count INT;
    high_quality INT;
    low_quality INT;
BEGIN
    SELECT COUNT(*) INTO total_count FROM widip_knowledge_base;
    SELECT COUNT(*) INTO high_quality FROM widip_knowledge_base WHERE quality_score >= 0.6;
    SELECT COUNT(*) INTO low_quality FROM widip_knowledge_base WHERE quality_score < 0.4;

    RAISE NOTICE '=== Statistiques après migration ===';
    RAISE NOTICE 'Total entrées: %', total_count;
    RAISE NOTICE 'Haute qualité (>=0.6): %', high_quality;
    RAISE NOTICE 'Basse qualité (<0.4): %', low_quality;
END $$;

-- =============================================================================
-- Migration terminée
-- =============================================================================
