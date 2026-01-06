import json
import uuid
import subprocess

# Load the workflow JSON
workflow_path = r"C:\Users\maxim\Desktop\Projet IA\WIDIP\Widip Clé 25-12-2025\Projet WIDIP IA\Constructions\WIBOT\wibot-backend\workflows\get_messages.json"

with open(workflow_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Extract required fields
name = workflow.get('name', 'Untitled')
nodes = json.dumps(workflow.get('nodes', []))
connections = json.dumps(workflow.get('connections', {}))
settings = json.dumps(workflow.get('settings', {}))
static_data = json.dumps(workflow.get('staticData'))
pin_data = json.dumps(workflow.get('pinData', {}))

# Generate IDs
workflow_id = 'msg' + str(uuid.uuid4())[:13].replace('-', '')
version_id = str(uuid.uuid4())

# Escape for PostgreSQL - double single quotes
def escape_sql(s):
    return s.replace("'", "''")

nodes_escaped = escape_sql(nodes)
connections_escaped = escape_sql(connections)
settings_escaped = escape_sql(settings)
static_data_escaped = escape_sql(static_data)
pin_data_escaped = escape_sql(pin_data)

# Build the INSERT SQL
sql = f"""
INSERT INTO workflow_entity (id, name, active, nodes, connections, settings, "staticData", "pinData", "versionId", "triggerCount")
VALUES (
    '{workflow_id}',
    '{escape_sql(name)}',
    true,
    '{nodes_escaped}'::json,
    '{connections_escaped}'::json,
    '{settings_escaped}'::json,
    '{static_data_escaped}'::json,
    '{pin_data_escaped}'::json,
    '{version_id}',
    1
);
"""

# Write to a file
sql_file = r"C:\Users\maxim\Desktop\Projet IA\WIDIP\Widip Clé 25-12-2025\Projet WIDIP IA\Constructions\WIBOT\wibot-backend\insert_workflow.sql"
with open(sql_file, 'w', encoding='utf-8') as f:
    f.write(sql)

print(f"SQL file created: {sql_file}")
print(f"Workflow ID: {workflow_id}")
