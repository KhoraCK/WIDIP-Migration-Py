-- Script pour mettre à jour le workflow WIBOT - Chat Main
-- Corrige la requête Check Quota pour gérer les nouveaux utilisateurs

-- D'abord, récupérer le workflow actuel
\set workflow_file 'workflows/chat_main.json'

-- Supprimer l'ancien workflow inactif
DELETE FROM workflow_entity WHERE name = 'WIBOT - Chat Main' AND active = false;

-- Désactiver l'ancien workflow actif
UPDATE workflow_entity
SET active = false
WHERE name = 'WIBOT - Chat Main' AND active = true;

-- Le nouveau workflow sera importé via l'interface n8n ou import_new_workflows.sql

\echo 'Ancien workflow désactivé. Veuillez réimporter le workflow via n8n.'
