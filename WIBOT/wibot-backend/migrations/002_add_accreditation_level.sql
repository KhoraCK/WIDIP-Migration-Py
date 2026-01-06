-- ===========================================
-- Migration: Ajouter accreditation_level aux users
-- Version: 002
-- Date: 2026-01-05
-- Description: Ajoute le niveau d'accreditation Safeguard (N0-N4)
-- ===========================================

-- Ajouter la colonne si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'accreditation_level'
    ) THEN
        ALTER TABLE users ADD COLUMN accreditation_level VARCHAR(2) DEFAULT 'N1';

        -- Ajouter la contrainte CHECK
        ALTER TABLE users ADD CONSTRAINT check_accreditation_level
            CHECK (accreditation_level IN ('N0', 'N1', 'N2', 'N3', 'N4'));

        RAISE NOTICE 'Colonne accreditation_level ajoutee avec succes';
    ELSE
        RAISE NOTICE 'Colonne accreditation_level existe deja';
    END IF;
END $$;

-- Mettre a jour les admins existants vers N4 (Super Admin)
UPDATE users
SET accreditation_level = 'N4'
WHERE role = 'admin' AND (accreditation_level IS NULL OR accreditation_level = 'N1');

-- Mettre a jour les users sans niveau vers N1 (Technicien)
UPDATE users
SET accreditation_level = 'N1'
WHERE accreditation_level IS NULL;

-- Verification
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM users WHERE accreditation_level IS NOT NULL;
    RAISE NOTICE 'Migration terminee: % utilisateurs avec niveau d''accreditation', v_count;
END $$;
