import json
import uuid
import os

workflows_to_import = [
    "rename_conversation.json",
    "delete_conversation.json"
]

base_path = r"C:\Users\maxim\Desktop\Projet IA\WIDIP\Widip Clé 25-12-2025\Projet WIDIP IA\Constructions\WIBOT\wibot-backend\workflows"
output_path = r"C:\Users\maxim\Desktop\Projet IA\WIDIP\Widip Clé 25-12-2025\Projet WIDIP IA\Constructions\WIBOT\wibot-backend\import_new_workflows.sql"

def escape_sql(s):
    return s.replace("'", "''")

sql_statements = []

for workflow_file in workflows_to_import:
    workflow_path = os.path.join(base_path, workflow_file)

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    name = workflow.get('name', 'Untitled')
    nodes = json.dumps(workflow.get('nodes', []))
    connections = json.dumps(workflow.get('connections', {}))
    settings = json.dumps(workflow.get('settings', {}))
    static_data = json.dumps(workflow.get('staticData'))
    pin_data = json.dumps(workflow.get('pinData', {}))

    # Generate unique IDs
    workflow_id = name.lower().replace(' ', '').replace('-', '')[:8] + str(uuid.uuid4())[:8]
    version_id = str(uuid.uuid4())

    sql = f"""
-- Import: {name}
INSERT INTO workflow_entity (id, name, active, nodes, connections, settings, "staticData", "pinData", "versionId", "triggerCount")
VALUES (
    '{workflow_id}',
    '{escape_sql(name)}',
    true,
    '{escape_sql(nodes)}'::json,
    '{escape_sql(connections)}'::json,
    '{escape_sql(settings)}'::json,
    '{escape_sql(static_data)}'::json,
    '{escape_sql(pin_data)}'::json,
    '{version_id}',
    1
);

INSERT INTO shared_workflow ("workflowId", "projectId", "role", "createdAt", "updatedAt")
VALUES ('{workflow_id}', 'sxOW4Z7kldKTFN4J', 'workflow:owner', NOW(), NOW());

INSERT INTO workflow_history ("versionId", "workflowId", "authors", "createdAt", "updatedAt", nodes, connections, name, autosaved, description)
VALUES (
    '{version_id}',
    '{workflow_id}',
    'system',
    NOW(),
    NOW(),
    '{escape_sql(nodes)}'::json,
    '{escape_sql(connections)}'::json,
    '{escape_sql(name)}',
    false,
    NULL
);

UPDATE workflow_entity SET "activeVersionId" = '{version_id}' WHERE id = '{workflow_id}';
"""
    sql_statements.append(sql)
    print(f"Prepared: {name} (ID: {workflow_id})")

# Write all SQL to file
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql_statements))

print(f"\nSQL file created: {output_path}")
