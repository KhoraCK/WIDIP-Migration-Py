-- Insérer dans workflow_history
INSERT INTO workflow_history ("versionId", "workflowId", "authors", "createdAt", "updatedAt", nodes, connections, name, autosaved, description)
SELECT
    we."versionId",
    we.id,
    'system',
    NOW(),
    NOW(),
    we.nodes,
    we.connections,
    we.name,
    false,
    NULL
FROM workflow_entity we
WHERE we.id = 'msg5c740bd9db51'
ON CONFLICT DO NOTHING;

-- Mettre à jour activeVersionId dans workflow_entity
UPDATE workflow_entity
SET "activeVersionId" = "versionId"
WHERE id = 'msg5c740bd9db51' AND "activeVersionId" IS NULL;
