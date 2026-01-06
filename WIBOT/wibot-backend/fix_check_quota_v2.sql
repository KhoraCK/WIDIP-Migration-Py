-- ===================================================================
-- Script de correction du node "Check Quota" - Version 2 (avec jsonb_set)
-- ===================================================================

DO $$
DECLARE
    v_workflow_id TEXT;
    v_nodes_jsonb JSONB;
    v_new_query TEXT;
    v_node_index INT;
BEGIN
    -- Définir la nouvelle requête
    v_new_query := 'SELECT
  COALESCE(t.used_tokens, 0) as used_tokens,
  COALESCE(t.quota_tokens, 50000) as quota_tokens
FROM users u
LEFT JOIN user_token_usage t ON (t.user_id = u.user_id AND t.month = DATE_TRUNC(''month'', CURRENT_DATE))
WHERE u.user_id = {{ $json.userId }}
LIMIT 1;';

    -- Récupérer le workflow actif
    SELECT id, nodes::jsonb
    INTO v_workflow_id, v_nodes_jsonb
    FROM workflow_entity
    WHERE name = 'WIBOT - Chat Main' AND active = true
    LIMIT 1;

    IF v_workflow_id IS NULL THEN
        RAISE EXCEPTION 'Workflow WIBOT - Chat Main actif non trouvé';
    END IF;

    RAISE NOTICE 'Workflow trouvé: %', v_workflow_id;

    -- Trouver l'index du node "Check Quota"
    FOR v_node_index IN 0..(jsonb_array_length(v_nodes_jsonb) - 1)
    LOOP
        IF (v_nodes_jsonb->v_node_index->>'name') = 'Check Quota' THEN
            RAISE NOTICE 'Node Check Quota trouvé à l''index %', v_node_index;
            RAISE NOTICE 'Ancienne requête: %', substring(v_nodes_jsonb->v_node_index->'parameters'->>'query', 1, 50);

            -- Mettre à jour la requête
            v_nodes_jsonb := jsonb_set(
                v_nodes_jsonb,
                array[v_node_index::text, 'parameters', 'query'],
                to_jsonb(v_new_query)
            );

            RAISE NOTICE 'Nouvelle requête appliquée!';
            EXIT;
        END IF;
    END LOOP;

    -- Mettre à jour le workflow
    UPDATE workflow_entity
    SET nodes = v_nodes_jsonb::json
    WHERE id = v_workflow_id;

    RAISE NOTICE '✓ Node Check Quota mis à jour avec succès!';
    RAISE NOTICE '✓ La requête utilise maintenant un LEFT JOIN pour gérer les nouveaux utilisateurs';

EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Erreur lors de la mise à jour: %', SQLERRM;
        RAISE;
END $$;
