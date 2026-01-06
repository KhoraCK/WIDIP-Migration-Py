#!/usr/bin/env python3
"""
Script pour corriger la requête du node Check Quota dans le workflow Chat Main
"""
import json
import psycopg2

# Configuration PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'wibot',
    'user': 'widip',
    'password': 'widipbot2024'
}

# Nouvelle requête SQL qui utilise un LEFT JOIN
NEW_QUERY = """SELECT
  COALESCE(t.used_tokens, 0) as used_tokens,
  COALESCE(t.quota_tokens, 50000) as quota_tokens
FROM users u
LEFT JOIN user_token_usage t ON (t.user_id = u.user_id AND t.month = DATE_TRUNC('month', CURRENT_DATE))
WHERE u.user_id = {{ $json.userId }}
LIMIT 1;"""

def fix_check_quota():
    """Corrige le node Check Quota dans le workflow"""
    try:
        # Connexion à la base
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Récupérer le workflow actif
        cur.execute("""
            SELECT id, name, nodes
            FROM workflow_entity
            WHERE name = 'WIBOT - Chat Main' AND active = true
        """)

        result = cur.fetchone()
        if not result:
            print("❌ Workflow 'WIBOT - Chat Main' actif non trouvé")
            return False

        workflow_id, workflow_name, nodes_json = result
        nodes = json.loads(nodes_json)

        # Trouver et mettre à jour le node Check Quota
        updated = False
        for node in nodes:
            if node.get('name') == 'Check Quota':
                print(f"✓ Node 'Check Quota' trouvé (id: {node['id']})")
                print(f"  Ancienne requête: {node['parameters']['query'][:50]}...")
                node['parameters']['query'] = NEW_QUERY
                print(f"  Nouvelle requête: {NEW_QUERY[:50]}...")
                updated = True
                break

        if not updated:
            print("❌ Node 'Check Quota' non trouvé dans le workflow")
            return False

        # Mettre à jour le workflow
        cur.execute("""
            UPDATE workflow_entity
            SET nodes = %s::json
            WHERE id = %s
        """, (json.dumps(nodes), workflow_id))

        conn.commit()
        print(f"✓ Workflow '{workflow_name}' mis à jour avec succès!")
        print(f"  {cur.rowcount} ligne(s) affectée(s)")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print(" Correction du node Check Quota")
    print("=" * 60)
    fix_check_quota()
