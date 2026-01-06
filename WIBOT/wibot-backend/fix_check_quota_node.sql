-- ===================================================================
-- Script de correction du node "Check Quota" dans le workflow Chat Main
-- ===================================================================
-- Problème : La requête actuelle ne retourne pas de ligne pour les
-- nouveaux utilisateurs qui n'ont pas encore d'entrée dans user_token_usage
-- Solution : Utiliser un LEFT JOIN pour toujours retourner une ligne
-- ===================================================================

DO $$
DECLARE
    v_workflow_id TEXT;
    v_nodes_json JSON;
    v_nodes_text TEXT;
    v_old_query TEXT;
    v_new_query TEXT;
BEGIN
    -- Définir la nouvelle requête
    v_new_query := E'SELECT \n  COALESCE(t.used_tokens, 0) as used_tokens,\n  COALESCE(t.quota_tokens, 50000) as quota_tokens\nFROM users u\nLEFT JOIN user_token_usage t ON (t.user_id = u.user_id AND t.month = DATE_TRUNC(''month'', CURRENT_DATE))\nWHERE u.user_id = {{ $json.userId }}\nLIMIT 1;';

    -- Récupérer le workflow actif
    SELECT id, nodes::text
    INTO v_workflow_id, v_nodes_text
    FROM workflow_entity
    WHERE name = 'WIBOT - Chat Main' AND active = true
    LIMIT 1;

    IF v_workflow_id IS NULL THEN
        RAISE EXCEPTION 'Workflow WIBOT - Chat Main actif non trouvé';
    END IF;

    RAISE NOTICE 'Workflow trouvé: %', v_workflow_id;

    -- Remplacer l'ancienne requête par la nouvelle
    -- Pattern de l'ancienne requête à remplacer
    v_old_query := 'SELECT \n  COALESCE(used_tokens, 0) as used_tokens,\n  COALESCE(quota_tokens, 50000) as quota_tokens\nFROM user_token_usage\nWHERE user_id = {{ $json.userId }}\n  AND month = DATE_TRUNC(''month'', CURRENT_DATE)\nLIMIT 1;';

    -- Faire le remplacement
    v_nodes_text := REPLACE(v_nodes_text, v_old_query, v_new_query);

    -- Mettre à jour le workflow
    UPDATE workflow_entity
    SET nodes = v_nodes_text::json
    WHERE id = v_workflow_id;

    RAISE NOTICE 'Node Check Quota mis à jour avec succès!';
    RAISE NOTICE 'Nouvelle requête utilise un LEFT JOIN pour gérer les nouveaux utilisateurs';

EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Erreur lors de la mise à jour: %', SQLERRM;
        RAISE;
END $$;
